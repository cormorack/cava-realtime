import datetime
import time
import requests
import json
import threading
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
from cava_realtime.producer.settings import producer_settings

# logger = logging.getLogger(__name__)
# logging.root.setLevel(level=logging.INFO)

# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logging.root.addHandler(handler)

# time stamps are returned in time since 1900, so we subtract 70 years from
# the time output using the ntp_delta variable
ntp_epoch = datetime.datetime(1900, 1, 1)
unix_epoch = datetime.datetime(1970, 1, 1)
NTP_DELTA = (unix_epoch - ntp_epoch).total_seconds()

POOL = ThreadPoolExecutor()
API_USERNAME = producer_settings.ooi_username
API_TOKEN = producer_settings.ooi_token


# convert timestamps
def ntp_seconds_to_datetime(ntp_seconds):
    return datetime.datetime.utcfromtimestamp(ntp_seconds - NTP_DELTA).replace(
        microsecond=0
    )


class StreamProducer(threading.Thread):
    def __init__(
        self,
        ref,
        parameters,
        request_url,
        topic,
        instrument_name,
        last_time=0,
        kafka_producer=None,
        **kwargs,
    ):
        self.ref = ref
        self.thread_name = f"Thread-{self.ref}"
        self.parameters = parameters
        self.request_url = request_url
        self.topic = topic
        self.instrument_name = instrument_name
        self.last_time = last_time
        self._params = {"beginDT": None, "limit": 1000}
        self.__ooi_username = API_USERNAME
        self.__ooi_token = API_TOKEN
        self._begin_time = None
        self.requesting = False
        self._kafka_producer = kafka_producer
        self._killed = False

        threading.Thread.__init__(self, name=self.thread_name, daemon=True)

    def run(self):
        self.requesting = True
        if self._kafka_producer:
            self._run_producer()
        else:
            logger.info(
                self._display_status(
                    "Not started. Kafka producer object not found."
                )
            )

    def stop(self):
        self._killed = True
        while self.is_alive():
            continue
        logger.info(self._display_status("Stopped."))

    def get_id(self):

        # returns id of the respective thread
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def _display_status(self, status):
        return f"{self.thread_name}:{status}"

    def __repr__(self):
        return f"<Stream: {self.instrument_name} - {self.ref}>"

    def _get_future_data(self):
        auth = (self.__ooi_username, self.__ooi_token)
        return POOL.submit(
            requests.get, self.request_url, params=self._params, auth=auth
        )

    def _extract_keys(self, data):
        rdict = {key: [] for key in self.parameters}
        min_time = self.last_time
        for record in data:
            if record["time"] <= min_time:
                time_r = record["time"]
                time_r = ntp_seconds_to_datetime(time_r)
                time_r = time_r.strftime("%Y-%m-%d %H:%M:%S.000Z")
                logger.info(
                    self._display_status(
                        f"No new data found since {time_r}. Sending new request."
                    )
                )
                continue
            for key in self.parameters:
                rdict[key].append(record[key])
        logger.info(
            self._display_status(
                f"Found {len(rdict['time'])} new data points after filtering"
            )
        )
        return rdict

    def _send_data(self, data=None):
        stream = {"ref": self.ref, "data": data}
        data_bytes = json.dumps(stream).encode("utf-8")
        # print data points returned
        self._kafka_producer.send(self.topic, data_bytes)
        logger.info(self._display_status(f"Bytesize {len(data_bytes)}"))

    def _run_producer(self):
        logger.info(self._display_status("Started."))
        self._begin_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=10
        )
        while self.requesting:
            if self._killed:
                logger.info(self._display_status("Killing Thread"))
                break
            begin_time_str = self._begin_time.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

            self._params["beginDT"] = begin_time_str
            data_future = self._get_future_data()

            # poll until complete
            while not data_future.done:
                # while request not complete, yield control to event loop
                time.sleep(0.1)

            # request complete, if not 200, log error and try again
            response = data_future.result()
            if response.status_code != 200:
                logger.info(
                    self._display_status(
                        "Error fetching data: "
                        + str(response.json()["message"]["status"])
                    )
                )
                self._send_data()
                time.sleep(0.1)
                continue

            # store json response
            data = response.json()

            # use extract_keys function to inform users about whether
            # or not data is being returned. parse data in json response
            # for input parameter and corresponding timestamp
            data = self._extract_keys(data)

            # if no data is returned, try again
            if not data["time"]:
                time.sleep(0.1)
                continue

            # set beginDT to time stamp of last data point returned
            self.last_time = data["time"][-1]
            self._begin_time = ntp_seconds_to_datetime(self.last_time)
            data["time"] = list(
                map(
                    lambda t: ntp_seconds_to_datetime(t).isoformat(),
                    data["time"],
                )
            )
            self._send_data(data)
