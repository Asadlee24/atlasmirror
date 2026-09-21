const net = require('net');

function createProxy(localPort, remotePort, remoteHost) {
  let connId = 0;
  const server = net.createServer((socket) => {
    const id = ++connId;
    const clientAddr = socket.remoteAddress + ':' + socket.remotePort;
    console.log(`[Proxy :${localPort} #${id}] New connection from ${clientAddr}`);

    const remote = net.connect(remotePort, remoteHost);

    socket.pipe(remote);
    remote.pipe(socket);

    remote.on('connect', () => {
      console.log(`[Proxy :${localPort} #${id}] Connected to ${remoteHost}:${remotePort}`);
    });

    remote.on('error', (err) => {
      console.log(`[Proxy :${localPort} #${id}] Remote error: ${err.message}`);
      socket.destroy();
    });

    socket.on('error', (err) => {
      console.log(`[Proxy :${localPort} #${id}] Socket error: ${err.message}`);
      remote.destroy();
    });

    socket.on('close', () => {
      console.log(`[Proxy :${localPort} #${id}] Connection closed`);
    });
  });

  server.listen(localPort, '0.0.0.0', () => {
    console.log(`TCP Proxy active: 0.0.0.0:${localPort} -> ${remoteHost}:${remotePort} via WARP`);
  });
}

createProxy(8070, 8070, '199.231.187.97');
createProxy(2222, 22, '199.231.187.97');
