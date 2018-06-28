#!/usr/bin/env python3
import requests
import optparse
import re
import sys
import mpd
import os
from bs4 import BeautifulSoup
import logging
logger = logging.getLogger('netease-to-mpd')

headers = {
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
    'Referer': 'http://music.163.com/',
    'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8'
}

def init_logging():
    # logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    if not os.path.exists('log'):
        os.mkdir('log')
    ef = logging.FileHandler('log/error.log')
    ef.setLevel(logging.ERROR)
    wf = logging.FileHandler('log/warning.log')
    wf.set_name(logging.WARNING)
    logger.addHandler(ef)
    logger.addHandler(wf)
    # logger.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

def init_args(show_help=False):
    optParse = optparse.OptionParser()
    optParse.add_option('-i', '--id', action='store', type='int', dest='id', help='MusicID')
    optParse.add_option('-u', '--url', action='store', dest='url', help='MusicURL such as \'http://music.163.com/#/playlist?mid=xxx\'')
    optParse.add_option('-n', '--name', action='store', dest='pname', help='Playlist name in mpd')
    mpdsettings = optparse.OptionGroup(optParse, 'MPD settings')
    mpdsettings.add_option('-p', '--port', action='store', default=6600, type='int', dest='port', help='MPD port(default is 6600)')
    mpdsettings.add_option('-s', '--host', action='store', default='localhost', dest='host', help='MPD host(default is localhost)')
    optParse.add_option_group(mpdsettings)
    if show_help == True:
        logger.warning('No operation! Printing help infomation!')
        optParse.print_help()
        sys.exit(1)
    return optParse.parse_args()

def get_from_arg():
    arg,_ = init_args()
    pname = arg.pname
    mid = arg.id
    if mid == None:
        if arg.url != None:
            mid = getid(arg.url)
            logger.debug('Converted url to mid {}'.format(mid))
        else:
            init_args(show_help=True)
            # will exit
    port = arg.port
    host = arg.host
    pname = arg.pname
    return mid, pname, port, host

def getid(url):
    logger.debug('Converting url {}'.format(url))
    mid = re.findall('.+music.163.com/#/playlist\?mid=(.+)', url)
    if len(mid) < 1:
        logger.error('Convert FAILED')
        sys.exit(3)
    return mid[0]

def getpage(mid):
    req = requests.get('http://music.163.com/playlist', {'id': mid}, headers=headers)
    return req.content

def getartist(link):
    url = 'http://music.163.com{}'.format(link)
    cont = requests.get(url, headers=headers).content
    bs = BeautifulSoup(cont, 'lxml')
    return bs.head.title.string.split(' - ')[1]

def init_mpdclient(host, port):
    # start mpd session
    clt = mpd.MPDClient()
    clt.idletimeout = None
    clt.timeout = 1
    clt.connect(host, port)
    
    # check and clear
    if clt.mpd_version == None:
        logger.error('Connect to mpd server fail!')
        logger.error('Make sure your mpd server run on localhost:6600')
        sys.exit(2)
    clt.clear()
    return clt

def add_song(clt, name, link):
    def not_found_logging(name, link, arti):
        logger.warning('{} caonnot be found!'.format(name))
        logger.warning('This song info:')
        logger.warning('\tname: "{}"'.format(name))
        logger.warning('\tlink: http://music.163.com{}'.format(link))
        logger.warning('\tarti: "{}"'.format(arti))
        logger.warning('')
    
    def choose(name, link, i):
        print('Auto match failed! You can choose by yourself! Sorry~')
        tot = 0
        print('To match:')
        print('\tName: {}'.format(name))
        print('\tLink: http://music.163.com{}'.format(link))
        print('\tArtist: {}'.format(getartist(link)))
        print('\nChoices:')
        for now in i:
            print('\tID: {}'.format(tot))
            print('\t\tFile: {}'.format(now['file']))
            print('\t\tArtist: {}'.format(now['artist']))
            print('\t\tAlbum: {}'.format(now['album']))
            print('\t\tTrack: {}'.format(now['track']))
            tot = tot + 1
            num = input('Choice: ')
            return i[int(num)]
    
    fd = clt.find('title',name)
    if len(fd) == 1:
        clt.add(fd[0]['file'])
    elif len(fd) > 1:
        arti = getartist(link)
        rig = None
        cho = False
        for ss in fd:
            if ss['artist'] == arti:
                if rig:
                    cho = True
                    break
                    # has inconfident start choose()
                else:
                    rig = ss
        if rig == None:
            not_found_logging(name, link, arti)
            return
        if cho:
            rig = choose(name, link, fd)
        clt.add(rig['file'])
    else:
        not_found_logging(name, link, getartist(link))

def main():
    mid, pname, port, host = get_from_arg()
    # get the playlist on NetEase
    cont = getpage(mid)
    bs = BeautifulSoup(cont, 'lxml')
    lt = bs.select('#song-list-pre-cache')[0].select('ul')[0].select('li')
    clt = init_mpdclient(host, port)
    for li in lt:
        name = li.select('a')[0].string
        link = li.select('a')[0].get('href')
        add_song(clt, name, link)
    
    # write playlist
    logger.debug('Saving playlist...')
    if pname:
        clt.save(pname)
    else:
        pname = input('Press playlist name below: ')
        clt.save(pname)
    # clt.clear()   

if __name__ == '__main__':
    init_logging()
    main()
