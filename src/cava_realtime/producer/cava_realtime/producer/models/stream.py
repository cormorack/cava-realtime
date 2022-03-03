import datetime
import time
import httpx
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

API_USERNAME = producer_settings.ooi_username
API_TOKEN = producer_settings.ooi_token


# convert timestamps
def ntp_seconds_to_datetime(ntp_seconds):
    return datetime.datetime.utcfromtimestamp(ntp_seconds - NTP_DELTA).replace(
        microsecond=0
    )


class StreamProducer:
    def __init__(
        self,
        ref,
        parameters,
        request_url,
        topic,
        instrument_name,
        client,
        last_time=0,
        kafka_producer=None,
    ):
        self.ref = ref
        self.parameters = parameters
        self.request_url = request_url
        self.topic = topic
        self.instrument_name = instrument_name
        self.last_time = last_time
        self._params = {
            'beginDT': None,
            'limit': 1000,
        }
        self._begin_time = None
        self._kafka_producer = kafka_producer
        self.client = client

    def __repr__(self):
        return f"<Stream: {self.instrument_name} - {self.ref}>"

    @property
    def request(self):
        return httpx.Request(
            method='GET', url=self.request_url, params=self._params
        )

    def _display_status(self, status):
        return f"{self.ref:<90}:{status:>50}"

    async def _get_future_data(self):
        response = await self.client.send(self.request)
        return response

    def _send_data(self, data=None):
        stream = {"ref": self.ref, "data": data}
        data_bytes = json.dumps(stream).encode("utf-8")
        logger.info(self._display_status(f"Bytesize {len(data_bytes)}"))
        if self._kafka_producer is not None:
            # print data points returned
            self._kafka_producer.send(
                self.topic, data_bytes, key=self.ref.encode("utf-8")
            )
        else:
            logger.info(
                self._display_status(
                    "Data not sent anywhere. Kafka producer object not found."
                )
            )

    def _extract_keys(self, data):
        rdict = {key: [] for key in self.parameters}
        min_time = self.last_time
        for record in data:
            if record['time'] <= min_time:
                time_r = record['time']
                time_r = ntp_seconds_to_datetime(time_r)
                time_r = time_r.strftime("%Y-%m-%d %H:%M:%S.000Z")
                logger.info(
                    self._display_status(
                        f'No new data found since {time_r}. Sending new request.'
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

    async def request_data(self):
        logger.info(
            self._display_status(
                f"Last requested: {ntp_seconds_to_datetime(self.last_time)}"
            )
        )
        self._begin_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=10
        )
        begin_time_str = self._begin_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        self._params['beginDT'] = begin_time_str
        # request complete, if not 200, log error and try again
        response = await self._get_future_data()
        if response.status_code != 200:
            logger.warning(
                self._display_status(str(response.json()['message']['status']))
            )
            return None
        try:
            # store json response
            data = response.json()

            # use extract_keys function to inform users about whether
            # or not data is being returned. parse data in json response
            # for input parameter and corresponding timestamp
            data = self._extract_keys(data)

            # if no data is returned, try again
            if not data["time"]:
                return None

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
        except Exception as e:
            logger.warning(self._display_status(f"Error found ({e})"))
            self._send_data()
            return None
        return data
