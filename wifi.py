from machine import UART, Pin
import uasyncio as asyncio
from primitives.delay_ms import Delay_ms

class ESP8266():
    def __init__(self, uart_n=0, timeout=500, debug=True):
        self.uart = UART(uart_n, baudrate=115200)
        self.debug = debug
        self.reader = asyncio.StreamReader(self.uart)
        self.writer = asyncio.StreamWriter(self.uart, {})
        self.timeout = timeout
        self.delay = Delay_ms()
        #self.serving = False
        #self.pending_connections = []
        self.pending_response = []
        asyncio.create_task(self._recv())

    async def _recv(self):
        while True: 
            resp = await self.reader.readline()
            if resp != None:
                resp = resp.decode().rstrip()
            if resp == '':
                continue
            self._debug(f'got: {resp}')
            self.pending_response.append(resp)
            # TODO if ack keyword (OK, FAIL, ERROR, others?) then don't restart timer, not sure how this works when serving connections...
            self.delay.trigger(self.timeout) 
            
    async def send(self, cmd, timeout = 0):
        if cmd is None or cmd == '':
            return []

        # TODO lock to avoid dumping resp (maybe if pending_response not empty?)
        while len(self.pending_response) != 0:
            self._debug('Pending response in progress, waiting...')
            asyncio.sleep(1)

        default_timeout = self.timeout
        if timeout > 0:
           self.timeout = timeout 
        await self.writer.awrite(f'{cmd}\r\n')
        self._debug(f'Sent: {cmd}')
        self.delay.trigger(self.timeout)
        while self.delay.running(): 
            await asyncio.sleep_ms(100)
        self.timeout = default_timeout
        out = self.pending_response
        self.pending_response = []
        return out


    def _debug(self, msg):
        if self.debug:
            print(msg)

    async def test(self):
        resp = await self.send('AT')
        return 'OK' in resp
