import json
from loguru import logger
from lxml import etree
import re
import threading
from cava_realtime.producer.obs_function import obs_bb_ground_acceleration, obs_bb_ground_velocity
from obspy.clients.seedlink.easyseedlink import create_client

OOI_NETWORK = 'OO'

IRIS_SITE_MAP = {
    'AXID1': 'RS03INT2-MJ03D-05-OBSSPA305',
    'AXEC1': 'RS03ECAL-MJ03E-05-OBSSPA303',
    'AXEC3': 'RS03ECAL-MJ03E-08-OBSSPA304',
    'AXEC2': 'RS03ECAL-MJ03E-09-OBSBBA302',
    'AXCC1': 'RS03CCAL-MJ03F-06-OBSBBA301',
    'AXBA1': 'RS03AXBS-MJ03A-05-OBSBBA303',
    'AXAS2': 'RS03ASHS-MJ03B-05-OBSSPA302',
    'AXAS1': 'RS03ASHS-MJ03B-06-OBSSPA301',
    'HYS14': 'RS01SUM1-LJ01B-05-OBSBBA101',
    'HYS13': 'RS01SUM1-LJ01B-06-OBSSPA103',
    'HYS12': 'RS01SUM1-LJ01B-07-OBSSPA102',
    'HYS11': 'RS01SUM1-LJ01B-08-OBSSPA101',
    'HYSB1': 'RS01SLBS-MJ01A-05-OBSBBA102',
}

ACCEL_LIST = [
    'AXBA1-HNE',
    'AXBA1-HNN',
    'AXBA1-HNZ',
    'AXCC1-HNE',
    'AXCC1-HNN',
    'AXCC1-HNZ',
    'AXEC2-HNE',
    'AXEC2-HNN',
    'AXEC2-HNZ',
    'HYS14-HNE',
    'HYS14-HNN',
    'HYS14-HNZ',
    'HYSB1-HNE',
    'HYSB1-HNN',
    'HYSB1-HNZ',
]


class ObsProducer(threading.Thread):
    def __init__(self, kafka_producer):
        self.thread_name = "Thread-seismology"
        self.requesting = False
        self._killed = False
        self._kafka_producer = kafka_producer
        self._client = None
        self._root = None

        self.setup_client()

        threading.Thread.__init__(self, name=self.thread_name, daemon=True)

    def setup_client(self):
        self._client = create_client(
            'rtserve.iris.washington.edu', on_data=self.handle_data
        )
        self._root = etree.fromstring(
            self._client.get_info('STREAMS').encode('utf-8')
        )

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

    def handle_data(self, trace):
        stream_name = '_'.join(
            [
                'iris',
                trace.meta.network,
                trace.meta.station,
                trace.meta.channel,
            ]
        ).lower()
        ref = '-'.join(
            [IRIS_SITE_MAP[trace.meta.station], 'streamed', stream_name]
        )

        if '-'.join([trace.meta.station, trace.meta.channel]) in ACCEL_LIST:
            data_param = 'ground_acceleration'
            ion_func = obs_bb_ground_acceleration
        else:
            data_param = 'ground_velocity'
            ion_func = obs_bb_ground_velocity

        result = {'ref': ref, 'data': {}}
        result['data']['time'] = list(trace.times('timestamp'))
        result['data'][data_param] = list(ion_func(trace.data))

        self._send_data(f"{ref}__raw", result)

    def _display_status(self, status):
        return f"{self.thread_name}:{status}"

    def _send_data(self, topic, result):
        data_bytes = json.dumps(result).encode("utf-8")
        # print data points returned
        self._kafka_producer.send(topic, data_bytes)
        logger.info(f"{topic} Sent: Bytesize {len(data_bytes)}")

    def _run_producer(self):
        logger.info(self._display_status("Started."))
        ooi_stations = [
            dict(channels=[c.attrib for c in s.getchildren()], **s.attrib)
            for s in self._root.xpath(f"//station[@network='{OOI_NETWORK}']")
        ]
        for st in ooi_stations:
            for chn in st['channels']:
                channel = chn['seedname']
                if re.match(r'\wH\w', channel):
                    network = st['network']
                    station = st['name']
                    if station in IRIS_SITE_MAP:
                        logger.info(station, channel)
                        self._client.select_stream(network, station, channel)

        self._client.run()
