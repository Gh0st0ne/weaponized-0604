from __future__ import print_function
import json
import base64
import string
import binascii
import dnslib

_dec = binascii.a2b_hex
width = 60

# input file: exported from Burp Extension "Taborator"
def decode_file(filename):
    with open(filename, 'rb') as f:
        records = json.load(f)
    return decode(list(records['interactionHistory'].values()))

# required #1
def decode(records, verb=False):
    _result = ''
    result = dict()
    records = filter(isValidBlock, records)
    record_num = len(records)
    if verb: print('Total record: %d' % record_num)
    if record_num == 0: return ''

    for item in records:
        if verb: print(item)
        idx, data = extractHex(item)
        if verb: print((idx, data))
        result[idx] = data

    maxStartOffset = max(result.keys())
    transferComplete = True
    for i in range(0, maxStartOffset, width):
        if i in result:
            _result += _dec(result[i])
        else:
            _result += '*' * width
            transferComplete = False
    _result += _dec(result[maxStartOffset])
    return transferComplete and width < result[maxStartOffset], _result

# dns record with <offset>.<encoded data>.XXXXXXX.burpcollaborator.net
def isValidBlock(record):
    if record['type'] == 'DNS':
        q = base64.b64decode(record['raw_query'])
        v = dnslib.DNSRecord().parse(q)
        fqdn = v.get_q().qname.idna().rstrip('.')
        labels = fqdn.split('.')
        return len(labels) == 5 and labels[0].isdigit() and all(c in string.hexdigits for c in labels[1])
    elif record['type'] == 'HTTP':
        print('\nGet HTTP Interaction: ', end='')
        req = base64.b64decode(record['request'])
        body = '\r\n'.join(req.split('\r\n\r\n')[1:])
        print(body)

    return False

# return sample: (0, '68656c6c6f')
def extractHex(record):
    q = base64.b64decode(record['raw_query'])
    v = dnslib.DNSRecord().parse(q)
    fqdn = v.get_q().qname.idna().rstrip('.')
    labels = fqdn.split('.')
    return int(labels[0]), labels[1]


if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    result_all = decode_file(filename)
    print("\n\n")
    print(result_all)
