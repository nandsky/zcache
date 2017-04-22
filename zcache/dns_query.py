# -*- coding: utf8 -*-

import dns.resolver


# 关于DNS
# host,dig,会忽略/etc/hosts文件，直接查询dnsserver，但是chrome不会

# 本地DNS，关闭递归查询
CDN_NAMESERVERS = "127.0.0.1"

my_resolver = dns.resolver.Resolver()
my_resolver.nameservers = [CDN_NAMESERVERS]



def get_a_record(hostname):
    try:
        record = my_resolver.query(hostname, "A")
    except dns.resolver.NoNameservers:
        return None

    c = len(record)
    if c < 1:
        return None


    return record[c-1].to_text()

def main():
    print get_a_record("www.jd.com")
    print get_a_record("baidu.com")

if __name__ == '__main__':
    main()