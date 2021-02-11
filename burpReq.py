import codecs
import requests
try:
    from urlparse import unquote
except:
    from urllib.parse import unquote

def parse(fname):
    # POST / HTTP/1.1
    #
    # extract ... from burp Request
    #  Headers
    #  Body
    headers = {}
    data = {}
    files = {}
    with codecs.open(fname, encoding='utf8') as f:
        head = f.readline()
        method, path, proto = head.split(' ')
        # process header
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            if line == '':  break
            key, value = line.split(':', 1)
            headers[key] = value.strip()

        # process body
        if 'Content-Type' in headers and headers['Content-Type'].startswith('multipart/form-data'):
            ct = headers['Content-Type']
            boundary = ct[ct.find('boundary=') + len('boundary='):]
            '''
                phase 0:  find boundary
                phase 1:  parse Content-Disposition, name, filename ...
                phase 2:  read all Value

                requests files input: {Name: (filename, data, content_type, headers)}
            '''
            phase = 0
            varNames = {}
            val = ''
            while phase != 4:
                line = f.readline().rstrip('\n').rstrip('\r')
                if line.startswith('--' + boundary):
                    if phase == 0:
                        varNames.clear()
                        val = ''
                    elif phase == 2:
                        files[varNames['name']] = (varNames.get('filename'), val[:-2], varNames.get('Content-Type'))
                        varNames.clear()
                        val = ''

                    if line.endswith('--'):
                        phase = 4
                    else:
                        phase = 1
                    continue
                elif phase == 1:
                    for field in line.split('; ')[1:]:
                        k, v = field.split('=')
                        assert v[0] == '"' and v[-1] == '"', 'multi-part parse error: ' + v
                        varNames[k] = v[1:-1]
                    probe = f.readline()
                    if probe.startswith('Content-Type'):
                        varNames['Content-Type'] = probe.split(':')[1].strip()
                        f.readline()
                    phase = 2
                    continue
                elif phase == 2:
                    val += line + '\r\n'
                
            del headers['Content-Type']
        else:
            for line in f:
                line = line.rstrip('\n').rstrip('\r')
                if line == '':  continue
                for param in filter(None, line.split('&')):
                    key, value = param.split('=', 1)
                    data[unquote(key)] = unquote(value.replace('+', '%20'))
    return method, headers['Host'] + path, headers, data, files

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        r = parse(sys.argv[1])
    else:
        r = parse(raw_input(" Enter your burp request file> ").strip())
    print(r[4])
