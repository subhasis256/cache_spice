def read_mt0(filename):
    fp = open(filename)
    lastline = ""
    lastline2 = ""
    while True:
        line = fp.readline()
        if line.startswith(".TITLE"):
            break

    header = fp.readline()
    fields = header.strip().split()
    stats = []

    while True:
        line = fp.readline()
        if not line:
            break
        vals = line.strip().split()
        stats.append({k:v for k,v in zip(fields,vals)})
    fp.close()
    return stats

def spice_format(x):
    if x < 1e-15:
        return '0.00'
    elif x < 1e-12:
        return '%.3ff'%(x*1e15,)
    elif x < 1e-9:
        return '%.3fp'%(x*1e12,)
    elif x < 1e-6:
        return '%.3fn'%(x*1e9,)
    elif x < 1e-3:
        return '%.3fu'%(x*1e6,)
    elif x < 1:
        return '%.3fm'%(x*1e3,)
    else:
        return '%.3f'%(x,)

