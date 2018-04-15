import requests


class LogicalLoad(object):
    def __init__(self, data):
        """Initialize the light."""
        self._data = data
        self._lightpads = []
        self._metrics = None
        self.event_listeners = {}

    @property
    def llid(self):
        return self._data['llid']

    @property
    def lpids(self):
        return self._data['lpids']

    @property
    def lightpads(self):
        return self._lightpads

    @property
    def name(self):
        return self._data['logical_load_name']

    @property
    def rid(self):
        return self._data['rid']

    @property
    def room_name(self):
        return self._data['room']['room_name']

    @property
    def primaryLightpad(self):
        return self.lightpads[0]  # TODO Who is primary? Most power usage?

    @property
    def dimmable(self):
        return bool(self.primaryLightpad.glow_enabled)

    @property
    def level(self):
        return self._metrics['level']

    @property
    def power(self):
        return sum(map(lambda p: p['power'], self._metrics['lightpad_metrics']))

    def add_lightpad(self, lightpad):
        self._lightpads.append(lightpad)
        lightpad.set_logical_load(self)
        lightpad.add_event_listener('power', self.power_event)
        lightpad.add_event_listener('dimmerchange', self.dimmerchange_event)

    def add_event_listener(self, event_type, listener):
        for lightpad in self._lightpads:
            lightpad.add_event_listener(event_type, listener)

    def changes_event(self, event):
        self._data['config'] = event['changes']

    def power_event(self, event):
        lpid = event['lpid']
        watts = event['watts']
        for metric in self._metrics['lightpad_metrics']:
            if (metric['lpid'] == lpid):
                metric['power'] = watts

    def dimmerchange_event(self, event):
        lpid = event['lpid']
        level = event['level']
        self._metrics['level'] = level
        for metric in self._metrics['lightpad_metrics']:
            if metric['lpid'] == lpid:
                metric['level'] = level

    def turn_on(self, level=None):
        if level is None:
            level = 255  # TODO handle default value?
        self.set_logical_load_level(level)

    def turn_off(self):
        self.set_logical_load_level(0)

    async def load_metrics(self):
        try:
            lightpad = self.primaryLightpad
            url = "https://%s:%s/v2/getLogicalLoadMetrics" % (lightpad.ip, lightpad.port)
            data = {
                "llid": self.llid
            }
            response = lightpad.post(url, data)

            if response.status_code is 200:
                metrics = response.json()
                metrics['level'] = max(map(lambda l: l['level'], metrics['lightpad_metrics']))
                self._metrics = metrics
                return metrics
            else:
                print("Failed to getLogicalLoadMetrics", data, response)

        except IOError:
            print('error')

    def set_logical_load_level(self, level):
        lightpad = self.primaryLightpad
        url = "https://%s:%s/v2/setLogicalLoadLevel" % (lightpad.ip, lightpad.port)
        data = {
            "level": level,
            "llid": self.llid
        }
        response = lightpad.post(url=url, data=data)

        if response.status_code is 204:
            return
        else:
            print("Failed to setLogicalLoadLevel", data, response)
