from aiohttp import web
import asyncio
import json
import logging.handlers

routes = web.RouteTableDef()


# сканер портов
# --------------------------------------------------


async def check_port(ip, port):
    conn = asyncio.open_connection(ip, port)
    try:
        reader, writer = await asyncio.wait_for(conn, timeout=3)
        return {'PORT': port, 'STATE': 'Open'}
    except Exception as e:
        return {'PORT': port, 'STATE': 'Close'}
    finally:
        if 'writer' in locals():
            writer.close()


async def check_port_sem(sem, ip, port):
    async with sem:
        try:
            return await check_port(ip, port)
        except asyncio.TimeoutError:
            return None


async def run(destinations, ports):
    sem = asyncio.Semaphore(400)
    tasks = [asyncio.ensure_future(check_port_sem(sem, d, p)) for d in destinations for p in ports]
    responses = await asyncio.gather(*tasks)
    return responses


# --------------------------------------------------


@routes.get('/scan/{ip}/{begin_port}/{end_port}')
async def handle(request):
    ip_address = [request.match_info['ip']]
    begin_port = request.match_info['begin_port']
    end_port = request.match_info['end_port']

    # Вызов функции
    ports = [i for i in range(int(begin_port), int(end_port) + 1)]
    response_obj = await run(ip_address, ports)

    return web.Response(text=json.dumps(response_obj))


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routes)

    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    my_logger.addHandler(handler)

    web.run_app(app)
