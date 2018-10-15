class LogicalLoad(object):
    def __init__(self, data):
        """Initialize the light."""
        self._data = data
        self._lightpads = []
        self._metrics = None

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

    async def turn_on(self, level=None):
        if level is None:
            if 'defaultLevel' in self.primaryLightpad.config:
                level = self.primaryLightpad.config['defaultLevel']
            else:
                level = 255

        await self.set_logical_load_level(level)

    async def turn_off(self):
        await self.set_logical_load_level(0)

    async def load_metrics(self):
        try:
            lightpad = self.primaryLightpad
            url = "https://%s:%s/v2/getLogicalLoadMetrics" % (lightpad.ip, lightpad.port)
            data = {
                "llid": self.llid
            }
            response = await lightpad.post_async(url, data)

            if response.status is 200:
                metrics = await response.json(content_type=None)
                metrics['level'] = max(map(lambda l: l['level'], metrics['lightpad_metrics']))
                self._metrics = metrics
                return metrics
            else:
                print("Failed to getLogicalLoadMetrics", data, response)

        except IOError:
            print('error')

    async def set_logical_load_level(self, level):
        lightpad = self.primaryLightpad
        url = "https://%s:%s/v2/setLogicalLoadLevel" % (lightpad.ip, lightpad.port)
        data = {
            "level": level,
            "llid": self.llid
        }
        response = await lightpad.post_async(url=url, data=data)

        return True if response.status is 204 else False

