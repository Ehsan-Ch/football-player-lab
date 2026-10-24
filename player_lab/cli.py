import argparse
def main():
    parser=argparse.ArgumentParser(description='Touchline football player analysis')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare').add_argument('--data',default='data')
    b=sub.add_parser('build');b.add_argument('--data',default='data');b.add_argument('--output',default='reports/results.json')
    sub.add_parser('serve').add_argument('--port',type=int,default=8788)
    args=parser.parse_args()
    if args.command=='prepare':
        from .data import prepare
        prepare(args.data)
    elif args.command=='build':
        from .analysis import build
        build(args.data,args.output)
    else:
        from .server import serve
        serve(args.port)
if __name__=='__main__':main()
