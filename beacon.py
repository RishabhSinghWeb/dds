import socket, json, time, select, sys, uuid, hashlib, random
from qbittorrent import Client
import bencoding, binascii, hashlib
from io import BytesIO
import os, platform, subprocess, psutil, cpuinfo#netifaces

# import stun
# nat_type, external_ip, external_port = stun.get_ip_info()
# print(nat_type, external_ip, external_port)


qb = Client("http://127.0.0.1:5555/")

torrents = {}  # torrents for each collection, like collection_id: [(torrent_file_name, download_status, infohash)]

# DIR = "../collection_files/"
DIR = "D:/collection_files/"
collection_files = ["aa.collection", "bb.collection"]
for collection in collection_files:
    path = DIR+collection
    paths = []
    try:
        with open(path, "r") as f:
            j = json.loads(f.read())
            torrent_files = []
            for torrent_file_name in j['torrents']:
                try:
                    with open(DIR+torrent_file_name, "rb") as f:
                        data = bencoding.bdecode(f.read())
                    infohash = hashlib.sha1(bencoding.bencode(data[b'info'])).hexdigest()
                except:
                    infohash = None
                torrent_files.append((torrent_file_name,False,infohash))  
            torrents[j['id']] = torrent_files
    except:
        print("can't open", path)

print('torrents:',torrents)
stats = {}
# exit()


class Torrent:

    # def create(path): # path of file or folder
    #     # create new torrent
    #     pass

    def download(path): # path of collection file
        # send api request to download torrent
        print("downloading",path)
        qb.download_from_file(open(DIR+path, "rb"), savepath=DIR)
        # qb.download_from_link(magnet_link)
        pass

    # def status(): # isDownloading or isDownloaded
    #     pass

    def delete(path, delete_files = False): # path of collection file
        # stop torrenting
        # delete files
        # delete torrent
        qb.delete(torrent["infohash_v1"])
        pass



WEBSITE_PORT = 9000
FLOOD_TIMER = 3 #28 # not 30 because 30*2=60 by that time peers already assume us offline
PEER_OFFLINE_TIME = 50 #60
CONCENSUS_INTERVAL = 15 #600
SYNC_INTERVAL = 12 #60

now = int(time.time())
consensus_timer = now - (CONCENSUS_INTERVAL - 5) # 5 sec delayed startup
last_sync_time = now - SYNC_INTERVAL + 5 # 5 sec delayed startup waiting for peers to connect
last_flood_time = 0


# starting sockets
host = '127.0.0.1' #'' # '0.0.0.0'
try:
    port = int(sys.argv[1])
    WEBSITE_PORT = port+1
except:
    port = 9000



sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((host, port))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock2 = socket.socket()
inputs = [sock]
print('Listening on udp %s:%s' % (host, port))
# print(host,port)

try:
    sock2.bind((host, WEBSITE_PORT))
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.listen(5)
    print('Listening on tcp %s:%s' % (host, WEBSITE_PORT))
    inputs.append(sock2)
except:
    print(f"WEBSITE_PORT:{WEBSITE_PORT} is not available")
    
# print(1,host,port)

# # get external ip address
# try:
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     s.settimeout(0)
#     s.connect(("8.8.8.8", 80))
#     host = s.getsockname()[0]
#     s.close()
#     print(2,host,port)

# except:
#     host = socket.gethostbyname((socket.gethostname()))
#     print(4,host,port)

# print(5,host,port)

# "type" deprecated everyone is beacon
peers = [
            {'type':'beacon', 'id':None, 'port':9000, 'time':now, 'host':'localhost'},
            {'type':'beacon', 'id':None, 'port':9000, 'time':now, 'host':host},
            {'type':'beacon', 'id':None, 'port':9000, 'time':now, 'host':'127.0.0.1'},
            # {'type':'beacon', 'id':None, 'port':9001, 'time':now, 'host':host},
            # {'type':'beacon', 'id':None, 'port':9001, 'time':now, 'host':"127.0.0.1"},
            # {'type':'beacon', 'id':None, 'port':9001, 'time':now, 'host':'localhost'},
            {'type':'beacon', 'id':None, 'port':9002, 'time':now, 'host':host},
            {'type':None, 'id':None, 'port':9010, 'time':now, 'host':host},
            {'type':'peer', 'id':None, 'port':9011, 'time':now, 'host':'localhost'},
            {'type':'peer', 'id':None, 'port':9012, 'time':now, 'host':'localhost'},
            {'type':'beacon', 'id':None, 'port':9003, 'time':now, 'host':'localhost'}
        ]

name = f'{str(port)} here!'

collections = [{"id":1, "files":[1,2,3,4,5]}]


# print(host,port)
# Main Loop
while True:
    now = int(time.time())
    # print(peers)
    # Clean up peers
    for peer in peers:
        if now - peer['time'] > PEER_OFFLINE_TIME: # remove those who have not sent FLOOD messages
            print('-',peer, peers)
            peers.remove(peer)
        elif peer['host'] == host and peer['port'] == port: # remove self from peer list
            peers.remove(peer)

    # Flood messages on Regular interval
    if now - last_flood_time > FLOOD_TIMER: 
        for peer in peers: # sent to all peers
            try:
                sock.sendto(json.dumps({
                    'type': 'FLOOD',
                    'host': host,
                    'port': port,
                    'id': str(uuid.uuid4()),
                    'name': name
                    }).encode(), (peer['host'],peer['port']))
                print("sent FLOOD to", host, port)
            except:
                print("Unable to reach peer: ", peer)
        last_flood_time = now

    # getting beacon stats
    if now - last_sync_time > SYNC_INTERVAL:
        # print(targets)
        for collection in targets:
            Torrent.download(targets[collection][0])
        for peer in peers:
            try:
                addr_req = (peer['host'], peer['port'])
                sock.sendto(json.dumps({
                        "type": "STATS"
                    }).encode(), addr_req)
            except:
                print("Unable to reach peer: ", peer)
        last_sync_time = now

    # Setting the target
    # print("stats",stats)
    t_stats = {}
    for addr in stats:
        s = stats[addr]
        for t_id in s:
        #     s[t_id]
            if t_id in t_stats:
                t_stats[t_id] = s[t_id] + t_stats[t_id].copy()
            else:
                t_stats[t_id] = s[t_id]
    c_stats = {}
    # print(">", t_stats)
    for t_id in t_stats:
        counter = {}
        x= t_stats[t_id]
        # print(x)
        for name,status,infohash in x:
    #         i = str(i)
            if name not in counter:
    #             print(0,name)
                counter[name] = 0
            if status:
    #             print("aa")
                counter[name] += 1
    #             print(counter)
        c_stats[t_id] = counter
    #     print(counter)
        
    # print(c_stats)

    targets = {}
    for c_stat in c_stats:
        sorted_stats = sorted(c_stats[c_stat].items(), key=lambda x:x[1])
        len(sorted_stats)
        if sorted_stats[0][1] > 3:
            continue
        targets[c_stat] = sorted_stats[0]

    # for addr in stats:
    #     t_stats = {}
    #     stat = stats[addr]
    #     _collections = stat
    #     for _collection_id in _collections:
    #         _collection = _collections[_collection_id]
    #         print("..", _collections)
    #         for t_id in _collections:
    #             t_stat = _collections[t_id] 
    #             if t_id in t_stats:

    #             t_stats['t_id']

    #     print(">>>",addr, stat)

    # Checking the pending process by checking torrent's completion progress

    # Consensus
    # On joining or get request - 5 second delayed from startup
    # if now - consensus_timer > CONCENSUS_INTERVAL:
    #     for peer in peers:
    #         try:
    #             sock.sendto(json.dumps({
    #                 'type': 'CONSENSUS'
    #                 }).encode(), (peer['host'],peer['port']))
    #         except:
    #             print("Unable to reach peer: ", peer)


    # getting pending torrents 


    # handling socket request
    read_sockets, write_sockets, error_sockets = select.select( inputs, inputs, [], 5)
    for client in read_sockets:

        # browser request
        if client.getsockname()[1] == WEBSITE_PORT:
            if client is sock2:  # New Connection
                clientsock, clientaddr = client.accept()
                inputs.append(clientsock)
            else:  # Existing Connection
                # print('Got request on', WEBSITE_PORT, 'from client:', client.getpeername())
                data = client.recv(1024)
                # print("CLIENT DATA", list(str(data[:6])), data)
                url = data.decode()[4:].split(" ")[0]
                print(url)
                if url == "/":
                    peers_table = "<thead><td>Who<td>Where<td>last_ping</thead>"
                    for peer in peers:
                        peers_table += f"""<tr><td>{peer['id']}</td><td>{peer['host']}:{peer['port']}</td>
                                            <td>{int(now-peer['time'])} seconds ago</td></tr>"""
                    collection_table = "<thead><td>Messages<td>Torrents<td>Hash</thead>"
                    # for block in blockcollection.Blockcollection[::-1]:
                    #     collection += f"<tr><td>{block.height}</td><td>{block}</td><td>{block}</td><td><ul>"
                    #     for message in block.messages:
                    #         collection += f"<li>{message}</li>"
                    #     collection += f"""</ul></td><td>{block.hash}</td><td>{}</td>
                    #                  <td>{block.timestamp}<br>{time.ctime(block.timestamp)}</td></tr>"""
                    
                    all_stats = "<h2>Stats</h2>"
                    for addr in stats:
                        stats_table = "<thead><td>Messages<td>Torrents<td>Hash</thead>"
                        stat = stats[addr]
                        for id in stat:
                            s = stat[id]
                            stats_table += f"<tr><td>{id}</td><td>{s}</td><tr>"
                        all_stats += f'<h4>{addr}</h4><table border="1">{stats_table}</table>'
                        # print('>',stat)
                    # send HTTP response to the browser
                    client.send(f"""HTTP/1.1 200 OK\nContent-Type: html\n\r\n\r\n
                            <head><meta http-equiv="refresh" content="3"></head>
                            <body>
                            <h1>Beacon Status</h1>
                            hosted on: {host}:{port}
                            <h2>Current peers</h2>
                            <table border="1">{peers_table}</table>
                            <h2>torrents to download</h2>
                            {targets}
                            <h3>Currently downloading</h3>{"downloading_queue"}
                            <h3>Downloading Overflow</h3>
                            <h2>The Collection</h2>
                            <table border="1">{collection_table}</table>
                            {all_stats}
                            <h4>Stats Counter</h4>{c_stats}
                            <style>table{{border-collapse:collapse}}thead{{text-align:center;font-weight: bold;}}</style>
                        """.encode())
                    client.close()
                    inputs.remove(client)
                elif url == "/api2":
                    print("<<><><><>>",stats)
                    st=[]
                    for addr in stats:
                        stat = stats[addr]
                        host,port = addr
                        st.append({'host':host,'port':port,'stat':stat})



                    kb = float(1024)
                    mb = float(kb ** 2)
                    gb = float(kb ** 3)

                    memTotal = int(psutil.virtual_memory()[0]/gb)
                    memFree = int(psutil.virtual_memory()[1]/gb)
                    memUsed = int(psutil.virtual_memory()[3]/gb)
                    memPercent = int(memUsed/memTotal*100)
                    storageTotal = int(psutil.disk_usage('/')[0]/gb)
                    storageUsed = int(psutil.disk_usage('/')[1]/gb)
                    storageFree = int(psutil.disk_usage('/')[2]/gb)
                    storagePercent = int(storageUsed/storageTotal*100)
                    info = cpuinfo.get_cpu_info()['brand_raw']
                    core = os.cpu_count()
                    host = socket.gethostname()
                    client.send((f"HTTP/1.1 200 OK\nContent-Type: application/json\nAccess-Control-Allow-Origin: *\n\r\n\r\n"+json.dumps({
                            'targets':targets,
                            'host':host,
                            'port':port,
                            'c_stats':c_stats,
                            'stats':st,
                            'peers':peers,
                            'collection_files': collection_files,

                            "proc_total" : len(psutil.pids()),
                            "load_avg_unit": "minutes",
                            "load_avg_1": round(psutil.getloadavg()[0],2),
                            "load_avg_5": round(psutil.getloadavg()[1],2),
                            "load_avg_15": round(psutil.getloadavg()[2],2),

                            # ---------- System Info ----------
                            "hostname":host,
                            "system":  platform.system(),
                            "machine": platform.machine(),
                            "kernel":  platform.release(),
                            "compiler":platform.python_compiler(),
                            "CPU":     info, 
                            "CPU_core":core, #"(Core)")
                            "memory":   memTotal,
                            "disk":     storageTotal,

                            "CPU_percent": psutil.cpu_percent(1),
                            # unit = GiB
                            "RAM_used": memUsed,
                            "RAM_total": memTotal,
                            "RAM_percent": memPercent,
                            "disk_used": storageUsed,
                            "disk_total": storageTotal,
                            "disk_percent": storagePercent,

                            #     active = netifaces.gateways()['default'][netifaces.AF_INET][1]
                            "speed" : psutil.net_io_counters(pernic=False),
                            "sent" : speed[0],
                            "psend" : round(speed[2]/kb, 2),
                            "precv" : round(speed[3]/kb, 2),

                            "packet_send"      : psend,
                            "packet_receive"   : precv,
                            # "KiB/s")
                        })).encode())
                    client.close()
                    inputs.remove(client)
                else:
                    client.send((f"HTTP/1.1 200 OK\nContent-Type: application/json\nAccess-Control-Allow-Origin: *\n\r\n\r\n"+json.dumps({
                            'torrents':qb.torrents(),
                            # 'stats':stats,
                            'c_stats':c_stats,
                            # 'counter':counter,
                            'collection_files': collection_files,
                            'comments': None,
                            'messages': None
                        })).encode())
                    client.close()
                    inputs.remove(client)


        # udp beacon/peer request
        else:
            try:
                data, addr = client.recvfrom(5*1024)
            except:
                continue
            print('recv %r - %r\n\n' % addr, data)
            req = json.loads(data.decode())

            if req['type'] == 'FLOOD':
                addr_req = (str(req['host'])), int(req['port'])
                for peer in peers:
                    # print("peer",peer)
                    if peer['host'] == req['host'] and peer['port'] == peer['port']: # old peer
                        peer['time'] = time.time()  # update time for clean up timeout
                        break
                else:  # new peer
                    peers.append({
                        'id': req['id'],
                        'port': int(req['port']),
                        'time': now,
                        'host': str(req['host']),
                        'name': req['name']
                        })

                try:
                    for peer in peers:
                        client.sendto(data, (peer.host, peer.port))
                except:
                    pass

                client.sendto(json.dumps({
                    'type': 'FLOOD_REPLY',
                    'host': host,
                    'port': port,
                    'name': name
                    }).encode(), addr_req) # not replied to sender i.e. addr


            elif req['type'] == 'STATS':
                # stats[addr] = 
                client.sendto(json.dumps({
                    "type": "STATS_REPLY",
                    "data": torrents
                    # 'height':blockcollection.height(),
                    # 'hash': block_hash
                    }).encode(),addr)

            elif req['type'] == 'STATS_REPLY':
                stats[addr] = req['data']

                # for stat in stats:
                #     if stat['addr'] == addr and stat['height'] == req['height'] and stat['hash'] == req['hash']:
                #         stat[time] = now
                #         break
                # else:
                #     req.pop('type')
                #     req['addr'] = addr
                #     req['time'] = now
                #     stats.append(req)

            elif req['type'] == 'GET_BLOCK':
                try:
                    client.sendto(blockcollection.Blockcollection[req['height']].json().encode(),addr)
                except:
                    client.sendto(json.dumps({
                            'hash':None,
                            'messages': None,
                            'timestamp': None,
                            'type': 'GET_BLOCK_REPLY'
                        }).encode(),addr)

            elif req['type'] == 'GET_BLOCK_REPLY':
                block = Block(req)
                if block.hash:
                    if blockcollection.append(block):
                        pass
                    else:
                        Blockcollection_buffer.append({'block':block, 'time':now})


