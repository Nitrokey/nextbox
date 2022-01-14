import sys

host = sys.argv[1]

conf = dict(
    active_host = host,
    active_proto = "http",

    user_pass = "j23cii932c09320c",
    user_login = "admin",
    proxy_domain = "daringer.nextbox.link",
    static_domain = "staticnextbox2.dedyn.io",
    email = "staticnextbox2@dadadada.33mail.com",
    dom = None,
    lvl = 0,
    max_lvl = 5,
)

def tracer(f):
    global conf
    def wrapped(*v, **kw):
        global conf
        
        pad = conf["lvl"] * "  "
        print (pad + f"[D ->]: {f.__name__}")
        conf["lvl"] += 1
        
        out = f(*v, **kw)
        
        suf = "(ok)" if out is not False else "(fail)"
        print (pad + f"[D <-]: {f.__name__} {suf}")
        conf["lvl"] -= 1
        
        return out
    return wrapped