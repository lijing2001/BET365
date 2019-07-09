
from twisted.internet import reactor

from modules import diffusion
 
def bet365():

    topics = [
        '__host',
        'CONFIG_10_0',
        'OVInPlay_10_0',
        'XL_L10_Z0_C1_W2',
    ]
    diffusion_client = diffusion.DiffusionClient(
        'wss://premws-pt3.365pushodds.com/zap/?uid=2678435589210',
        '1',
        session_url='https://www.653884.com/sports-configuration',
        protocol='zap-protocol-v1',
        headers={},
        topics=topics,
    )
    if diffusion_client.can_connect():
        try:
            diffusion_client.connect()
        except KeyboardInterrupt:
            diffusion_client.disconnect()
        except Exception:
            diffusion_client.disconnect()


def williamhill(id):
    headers = {
        'Origin': 'http://cachescoreboards.williamhill.com',
    }
    topics = [
        'sportsbook/football/%s/i18n/en-gb/commentary' % id,
        'sportsbook/football/%s/stats/away/cards/red' % id,
        'sportsbook/football/%s/stats/away/cards/yellow' % id,
        'sportsbook/football/%s/stats/away/corners' % id,
        'sportsbook/football/%s/stats/away/goals' % id,
        'sportsbook/football/%s/stats/away/penalties' % id,
        'sportsbook/football/%s/stats/away/shots/offTarget' % id,
        'sportsbook/football/%s/stats/away/shots/onTarget' % id,
        'sportsbook/football/%s/stats/away/shots/onWoodwork' % id,
        'sportsbook/football/%s/stats/away/substitutions' % id,
        'sportsbook/football/%s/stats/away/throwIns' % id,
        'sportsbook/football/%s/stats/home/cards/red' % id,
        'sportsbook/football/%s/stats/home/cards/yellow' % id,
        'sportsbook/football/%s/stats/home/corners' % id,
        'sportsbook/football/%s/stats/home/goals' % id,
        'sportsbook/football/%s/stats/home/penalties' % id,
        'sportsbook/football/%s/stats/home/shots/offTarget' % id,
        'sportsbook/football/%s/stats/home/shots/onTarget' % id,
        'sportsbook/football/%s/stats/home/shots/onWoodwork' % id,
        'sportsbook/football/%s/stats/home/substitutions' % id,
        'sportsbook/football/%s/stats/home/throwIns' % id,
        'sportsbook/football/%s/stats/homeTeamPossesion' % id,
        'sportsbook/football/%s/stats/period' % id,
        'sportsbook/football/%s/stats/time' % id,
    ]
    diffusion_client = diffusion.DiffusionClient(
        'wss://scoreboards-ssl.williamhill.com/diffusion?v=4&ty=WB',
        '4',
        session_url=None,
        protocol=None,
        headers=headers,
        topics=topics,
    )
    if diffusion_client.can_connect():
        try:
            diffusion_client.connect()
        except KeyboardInterrupt:
            diffusion_client.disconnect()
        except Exception:
            diffusion_client.disconnect()


if __name__ == '__main__':
        print('start...')
        bet365()       
        reactor.run()
