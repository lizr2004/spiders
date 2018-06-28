#!/usr/bin/env python3
import requests
import logging
import gzip
import re
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
logging.info('Started Bilibili Helper.')

def getcid(aid):
    page_url = "https://www.bilibili.com/video/av{}"
    page_url = page_url.format(aid)
    logging.info('page_url is: {}'.format(page_url))
    page_res = requests.get(page_url)
    page_str = page_res.content.decode('utf-8')
    cid_str = re.findall(r'cid=([0-9]+?)\&', page_str)
    cid = int(cid_str[0])
    return cid

def getchat(cid, get=True):
    chat_url = 'https://api.bilibili.com/x/v1/dm/list.so?oid={}'
    chat_url = chat_url.format(cid)
    if get:
        chat_res = requests.get(chat_url)
        return chat_url,chat_res.content
    else:
        return chat_url

def main(aid):
    cid = getcid(aid)
    logging.info('Got cid: {}.'.format(cid))
    chat_url,chat = getchat(cid, get=True)
    logging.info('Got chat infomation.')
    # print('Chat_url is {} .'.format(chat_url))
    open("{}.xml".format(aid), "wb").write(chat)
    
if __name__ == '__main__':
    for vid in vidlist:
        main(vid)