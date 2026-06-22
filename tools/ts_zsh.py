"""Binding to the locally-built from-scratch zsh grammar (parser.so in repo root)."""
import ctypes as C, os
_HERE = os.path.dirname(__file__)
_SO = os.path.join(_HERE, '..', 'parser.so')
_core = C.CDLL("/usr/lib/libtree-sitter.so")
_zsh = C.CDLL(_SO)
class TSNode(C.Structure):
    _fields_=[("context",C.c_uint32*4),("id",C.c_void_p),("tree",C.c_void_p)]
for n,a,r in [("ts_parser_new",[],C.c_void_p),("ts_parser_set_language",[C.c_void_p,C.c_void_p],C.c_bool),
 ("ts_parser_parse_string",[C.c_void_p,C.c_void_p,C.c_char_p,C.c_uint32],C.c_void_p),
 ("ts_tree_root_node",[C.c_void_p],TSNode),("ts_node_type",[TSNode],C.c_char_p),
 ("ts_node_start_byte",[TSNode],C.c_uint32),("ts_node_end_byte",[TSNode],C.c_uint32),
 ("ts_node_child_count",[TSNode],C.c_uint32),("ts_node_child",[TSNode,C.c_uint32],TSNode),
 ("ts_node_field_name_for_child",[TSNode,C.c_uint32],C.c_char_p),("ts_node_is_named",[TSNode],C.c_bool),
 ("ts_node_has_error",[TSNode],C.c_bool),("ts_node_is_missing",[TSNode],C.c_bool),
 ("ts_tree_delete",[C.c_void_p],None),("ts_parser_delete",[C.c_void_p],None)]:
    f=getattr(_core,n); f.argtypes=a; f.restype=r
_zsh.tree_sitter_zsh.restype=C.c_void_p
class Node:
    def __init__(s,ts,src,field=None):
        s._ts=ts; s._src=src; s.type=_core.ts_node_type(ts).decode(); s.field=field
        s.named=_core.ts_node_is_named(ts); s.start=_core.ts_node_start_byte(ts); s.end=_core.ts_node_end_byte(ts)
        s.missing=_core.ts_node_is_missing(ts)
    @property
    def text(s): return s._src[s.start:s.end].decode("utf-8","replace")
    @property
    def children(s):
        out=[]
        for i in range(_core.ts_node_child_count(s._ts)):
            ch=_core.ts_node_child(s._ts,i); fn=_core.ts_node_field_name_for_child(s._ts,i)
            out.append(Node(ch,s._src,fn.decode() if fn else None))
        return out
    def sexp(s,d=0,maxd=6):
        f=f"{s.field}: " if s.field else ""; pad="  "*d
        line=f"{pad}{f}{s.type}"
        if s.named and not [c for c in s.children if c.named]: line+=f"  «{s.text[:40]}»"
        ls=[line]
        if d<maxd:
            for c in s.children:
                if c.named or c.field: ls.append(c.sexp(d+1,maxd))
        return "\n".join(ls)
class Parser:
    def __init__(s):
        s.p=_core.ts_parser_new(); _core.ts_parser_set_language(s.p,_zsh.tree_sitter_zsh())
    def parse(s,src):
        if isinstance(src,str): src=src.encode("utf-8")
        t=_core.ts_parser_parse_string(s.p,None,src,len(src)); return t,Node(_core.ts_tree_root_node(t),src)
    def free(s,t): _core.ts_tree_delete(t)
    def close(s): _core.ts_parser_delete(s.p)
def parse(src):
    P=Parser(); t,r=P.parse(src); return r
