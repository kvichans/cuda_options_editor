''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '2.1.1 2018-03-14'
ToDo: (see end of file)
'''

import  re, os, sys, json, collections, webbrowser, tempfile, html, pickle
from    itertools       import *
from pathlib import PurePath as PPath
from pathlib import     Path as  Path

import  cudatext            as app
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    .cd_plug_lib    import *

d   = dict
class odict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        if     args:super().__init__(*args)
        elif kwargs:super().__init__(kwargs.items())
    def __str__(self):
        return '{%s}' % (', '.join("'%s':%r" % (k,v) for k,v in self.items()))
    def __repr__(self):
        return self.__str__()
#odict = collections.OrderedDict

pass;                           LOG     = (-1==-1)          # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)
pass;                           ##!! waits correction

_   = get_translation(__file__) # I18N

MIN_API_VER_4WR = '1.0.175'     # vis
MIN_API_VER_4CL = '1.0.231'     # listview has prop columns
MIN_API_VER_4AG = '1.0.236'     # p, panel
VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')
#MIN_API_VER = '1.0.168'
MAX_HIST    = apx.get_opt('ui_max_history_edits', 20)
CFG_JSON    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_options_editor.json'
HTM_RPT_FILE= str(Path(tempfile.gettempdir()) / 'CudaText_option_report.html')

def parse_definitions(defn_path:Path)->list:
    """ Return  
            [{  opt:'opt name'
            ,   def:<def val>
            ,   cmt:'full comment'
            ,   frm:'bool'|'float'|'int'|'int2s'|'str'|'strs'|'str2s'|'font'|'hotk'|'json'      |'unk'
            ,   lst:[str]       for frm==ints
            ,   dct:[(num,str)] for frm==int2s
            ,       [(str,str)] for frm==str2s
            ,   chp:'chapter/chapter'
            ,   tgs:['tag',]
            }]
    """
    pass;                      #LOG and log('defn_path={}',(defn_path))
    kinfs    = []
    lines   = defn_path.open(encoding='utf8').readlines()
    if lines[0][0]=='[':
        # Data is ready - SKIP parsing
        return json.loads(defn_path.open().read(), object_pairs_hook=odict)

#   if 'debug'=='debug':        lines = ['  //[FindHotkeys]'
#                                       ,'  //Hotkeys in Find/Replace dialog'
#                                       ,'  "find_hotkey_find_first": "Alt+Enter",'
#                                       ,'  "find_hotkey_replace": "Alt+Z",'
#                                       ,'  "find_hotkey_find_dlg": "Ctrl+F",'
#                                       ,'  '
#                                       ,'  //UI elements font name [has suffix]'
#                                       ,'  "ui_font_name": "default",'
#                                       ]

    l       = '\n'
    
    #NOTE: parse_raw
    reTags  = re.compile(r' *\((#\w+,?)+\)')
    reN2S   = re.compile(r'^\s*(\d+): *(.+)'    , re.M)
    reS2S   = re.compile(r'^\s*"(\w*)": *(.+)'  , re.M)
    reLike  = re.compile(r' *\(like (\w+)\)')               ##??
    reFldFr = re.compile(r'\s*Folders from: (.+)')
    def parse_cmnt(cmnt, frm, kinfs):  
        tags= set()
        mt  = reTags.search(cmnt)
        while mt:
            tags_s  = mt.group(0)
            tags   |= set(tags_s.strip(' ()').replace('#', '').split(','))
            cmnt    = cmnt.replace(tags_s, '')
            mt      = reTags.search(cmnt)
        dctN= [[int(m.group(1)), m.group(2).rstrip(', ')] for m in reN2S.finditer(cmnt+l)]
        dctS= [[    m.group(1) , m.group(2).rstrip(', ')] for m in reS2S.finditer(cmnt+l)]
        frmK,\
        dctK= frm, None
        mt  = reLike.search(cmnt)
        if mt:
            ref_knm = mt.group(1)
            ref_kinf= [kinf for kinf in kinfs if kinf['key']==ref_knm]
            if not ref_kinf:
                log('Error on parse {}. No ref-key {} from comment\n{}',(path_to_raw, ref_knm, cmnt))
            else:
                ref_kinf = ref_kinf[0]
                frmK= ref_kinf['format']    if 'format' in ref_kinf else    frmK
                dctK= ref_kinf['dct']       if 'dct'    in ref_kinf else    dctK
        lstF= None
        mt  = reFldFr.search(cmnt)
        if mt:
            from_short  = mt.group(1)
            from_dir    = from_short if os.path.isabs(from_short) else os.path.join(app.app_path(app.APP_DIR_DATA), from_short)
            pass;              #LOG and log('from_dir={}',(from_dir))
            if not os.path.isdir(from_dir):
                log(_('No folder "{}" from\n{}'), from_short, cmnt)
            else:
                lstF    = [d for d in os.listdir(from_dir) if os.path.isdir(from_dir+os.sep+d)]
        frm,\
        lst = ('strs' , lstF)    if lstF else \
              (frm    , []  )
        frm,\
        dct = ('int2s', dctN)    if dctN else \
              ('str2s', dctS)    if dctS else \
              (frmK   , dctK)    if dctK else \
              (frm    , []  )
#             ('str2s', dctF)    if dctF else 
        return cmnt, frm, dct, lst, list(tags)
       #def parse_cmnt
    def jsstr(s):
        return s[1:-1].replace(r'\"','"').replace(r'\\','\\')
    
    reChap1 = re.compile(r' *//\[Section: +(.+)\]')
    reChap2 = re.compile(r' *//\[(.+)\]')
    reCmnt  = re.compile(r' *//(.+)')
    reKeyDV = re.compile(r' *"(\w+)" *: *(.+)')
    reInt   = re.compile(r' *(-?\d+)')
    reFloat = re.compile(r' *(-?\d+\.\d+)')
    reFontNm= re.compile(r'font\w*_name')
    reHotkey= re.compile(r'_hotkey_')
    chap    = ''
    ref_cmnt= ''    # Full comment to add to '... smth'
    pre_cmnt= ''
    cmnt    = ''
    for line in lines:
        if False:pass
        elif    reChap1.match(line):
            mt= reChap1.match(line)
            chap    = mt.group(1)
            cmnt    = ''
        elif    reChap2.match(line):
            mt= reChap2.match(line)
            chap    = mt.group(1)
            cmnt    = ''
        elif    reCmnt.match(line):
            mt= reCmnt.match(line)
            cmnt   += l+mt.group(1)
        elif    reKeyDV.match(line):
            mt= reKeyDV.match(line)
            key     = mt.group(1)
            dval_s  = mt.group(2).rstrip(', ')
            cmnt    = cmnt.strip(l)     if cmnt else pre_cmnt
            dfrm,dval= \
                      ('bool', True         )   if dval_s=='true'                       else \
                      ('bool', False        )   if dval_s=='false'                      else \
                      ('float',float(dval_s))   if reFloat.match(dval_s)                else \
                      ('int',  int(  dval_s))   if reInt.match(dval_s)                  else \
                      ('font', dval_s[1:-1] )   if reFontNm.search(key)                 else \
                      ('hotk', dval_s[1:-1] )   if reHotkey.search(key)                 else \
                      ('str',  jsstr(dval_s))   if dval_s[0]=='"' and dval_s[-1]=='"'   else \
                      ('unk',  dval_s       )
            pass;              #LOG and log('key,dval_s,dfrm,dval={}',(key,dval_s,dfrm,dval))
            
            ref_cmnt= ref_cmnt                                      if cmnt.startswith('...') else cmnt
            kinf    = odict()
            kinfs  += [kinf]
            kinf['opt']         = key
            kinf['def']         = dval
            kinf['cmt']         = cmnt.strip()
            kinf['frm']         = dfrm
            if dfrm in ('int','str'):
                cmnt,frm,\
                dct,lst,tags    = parse_cmnt(ref_cmnt+l+cmnt[3:]    if cmnt.startswith('...') else cmnt, dfrm, kinfs)
                kinf['cmt']     = cmnt.strip()
                if frm!=dfrm:
                    kinf['frm'] = frm
                if dct:
                    kinf['dct'] = dct
                if lst:
                    kinf['lst'] = lst
                if tags:
                    kinf['tgs'] = tags
            if chap:
                kinf['chp']     = chap
            
            pre_cmnt= cmnt              if cmnt else pre_cmnt
            cmnt    = ''
       #for line
    upd_cald_vals(kinfs, '+def')
    for kinf in kinfs:
        kinf['jdc'] = kinf.get('jdc', kinf.get('dct', []))
        kinf['jdf'] = kinf.get('jdf', kinf.get('def', ''))
    return kinfs
   #def parse_definitions

def load_vals(opt_dfns:list, lexr_json='', full=False)->odict:
    """ Create reformated copy (as odict) of 
            definitions data opt_dfns (see parse_definitions) 
        If full==True then append optitions without definition
            but only with 
            {   opt:'opt name'
            ,   frm:'int'|'float'|'str'
            ,   uval:<value from user.json>
            ,   lval:<value from lexer*.json>
            }}
        Return
            {'opt name':{  opt:'opt name', frm:
        ?   ,   def:, cmt:, dct:, chp:, tgs:
        ?   ,   uval:<value from user.json>
        ?   ,   lval:<value from lexer*.json>
        ?   ,   eval:<value from ed>
            }}
    """
    user_json       = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'user.json'
    user_vals       = apx._json_loads(open(user_json, encoding='utf8').read(), object_pairs_hook=odict) \
                        if os.path.isfile(user_json) else {}
    lexr_vals       = {}
    lexr_json       = app.app_path(app.APP_DIR_SETTINGS)+os.sep+lexr_json
    if lexr_json and os.path.isfile(lexr_json):
        lexr_vals   = apx._json_loads(open(lexr_json, encoding='utf8').read(), object_pairs_hook=odict)
    else:
        pass;                   LOG and log('no lexr_json={}',(lexr_json))
    edit_vals       = get_ovrd_ed_opts(ed)
    pass;                      #LOG and log('lexr_vals={}',(lexr_vals))

    # Fill vals for defined opt
    oinf_valed  = odict([(oi['opt'], oi) for oi in opt_dfns])
    for opt, oinf in oinf_valed.items():
        if opt in user_vals:        # Found user-val for defined opt
            oinf['uval']    = user_vals[opt]
        if opt in lexr_vals:        # Found lexer-val for defined opt
            oinf['lval']    = lexr_vals[opt]
        if opt in edit_vals:        # Found lexer-val for defined opt
            oinf['eval']    = edit_vals[opt]

    if full:
        # Append item for non-defined opt
        reFontNm    = re.compile(r'font\w*_name')
        def val2frm(val, opt=''):
            pass;              #LOG and log('opt,val={}',(opt,val))
            return  ('bool'     if isinstance(val, bool)    else
                     'int'      if isinstance(val, int)     else
                     'float'    if isinstance(val, float)   else
                     'json'     if isinstance(val, list)    else
                     'hotk'     if '_hotkey_' in val        else
                     'font'     if reFontNm.search(val)     else
                     'str')
        for uop,uval in user_vals.items():
            if uop in oinf_valed: continue
            oinf_valed[uop] = odict(
                [   ('opt'  ,uop)
                ,   ('frm'  ,val2frm(uval,uop))
                ,   ('uval' ,uval)
                ]+([('lval' ,lexr_vals[uop])] if uop in lexr_vals else [])
                )
        for lop,lval in lexr_vals.items():
            if lop in oinf_valed: continue
            oinf_valed[lop] = odict(
                [   ('opt'  ,lop)
                ,   ('frm'  ,val2frm(lval,lop))
                ,   ('lval' ,lval)
                ])
    
    upd_cald_vals(oinf_valed)

    return oinf_valed
   #def load_vals

def upd_cald_vals(ois, what=''):
    # Fill calculated attrs
    if '+def' in what:
        for oi in [oi for oi in ois if 'dct' in oi]:
            dct = oi['dct']
            dval= oi['def']
            dc  = odict(dct)
            pass;              #LOG and log('dct={}',(dct))
            oi['jdc']   = [f('({}) {}', vl,   cm      ) for vl,cm in dct]
            oi['jdf']   =  f('({}) {}', dval, dc[dval])


    # Fill calculated attrs
    if not what or '+clcd' in what:
        for op, oi in ois.items():
            oi['!']     =('+!!' if  'def' not in oi and 'lval' in oi   else
                           '+!' if  'def' not in oi and 'uval' in oi   else
                           '!!' if                      'lval' in oi   else
                            '!' if                      'uval' in oi   else
                          '')
            dct         = odict(oi.get('dct', []))
            oi['juvl']  = oi.get('uval', '') \
                            if not dct or 'uval' not in oi else \
                          f('({}) {}', oi['uval'], dct[oi['uval']])
            oi['jlvl']  = oi.get('lval', '') \
                            if not dct or 'lval' not in oi else \
                          f('({}) {}', oi['lval'], dct[oi['lval']])
   #def upd_cald_vals

#class OptDt:
#   """ Options infos to view/change in dlg.
#       Opt getting is direct - by fields.
#       Opt setting only by methods.
#   """
#
#   def __init__(self
#       , keys_info=None            # Ready data
#       , path_raw_keys_info=''     # default.json
#       , path_svd_keys_info=''     # To save parsed default.json
#       , bk_sets=False             # Create backup of settings before the first change
#       ):
#       self.defn_path  = Path(path_raw_keys_info)
#       self.bk_sets    = bk_sets   # Need to backup
#       self.bk_files   = {}        # Created backup files
#
#       self.opts_defn  = {}        # Meta-info for options: format, comment, dict/list of values, chapter, tags
#       self.ul_opts    = {}        # Total options info for user+cur_lexer
#      #def __init__
#  
#  #class OptDt
   
class OptEdD:
    SCROLL_W= app.app_proc(app.PROC_GET_GUI_HEIGHT, 'scrollbar') if app.app_api_version()>='1.0.233' else 15
    COL_SEC = 0
    COL_NAM = 1
    COL_OVR = 2
    COL_DEF = 3
    COL_USR = 4
    COL_LXR = 5
    COL_NMS = (_('Section'), _('Option'), '!', _('Default value'), ('User value'), _('Lexer value'))
    COL_MWS = [70, 150, 25, 120, 120, 70]   # Min col widths
    COL_N   = len(COL_MWS)
    CMNT_MHT= 60                            # Min height of Comment

    FLTR_H  = _('Suitable options will contain all specified words.'
              '\r Tips and tricks:'
              '\r • Add "#" to search the words also in comments'
              '\r • Use "<" or ">" for word boundary.'
              '\r     Example: '
              '\r       size> <tab'
              '\r     selects "tab_size" but not "ui_tab_size" or "tab_size_x".'
              '\r • Add "!" to show only user options.'
              '\r     Pure "!" shows all assigned user options.'
              '\r • Add "!!" to show only lexer options.'
              '\r     Pure "!!" shows all assigned lexer options.'
              '\r • Add "@smth" to show only sections with "smth"'
              '\r • Alt+L - Clear filter')
    FONT_L  = ['default'] \
            + [font 
                for font in app.app_proc(app.PROC_ENUM_FONTS, '')
                if not font.startswith('@')] 

    
    def __init__(self
        , keys_info=None                    # Ready data
        , path_raw_keys_info=''             # default.json
        , path_svd_keys_info=''             # To save parsed default.json
        , subset=''                         # To get/set from/to cuda_options_editor.json
        ):
        M,m         = OptEdD,self
        m.defn_path = Path(path_raw_keys_info)
        m.subset    = subset
        m.stores    = json.loads(open(CFG_JSON).read(), object_pairs_hook=odict) \
                        if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                      odict()
        pass;                  #LOG and log('ok',())
#       m.bk_sets   = m.stores.get(m.subset+'bk_sets'    , False)
        m.lexr_l    = app.lexer_proc(app.LEXER_GET_LEXERS, False)
        m.lexr_w_l  = [f('{} {}'
                        ,'!!' if os.path.isfile(app.app_path(app.APP_DIR_SETTINGS)+os.sep+'lexer '+lxr+'.json') else '  '
                        , lxr) 
                        for lxr in m.lexr_l]
        
        m.col_ws    = m.stores.get(m.subset+'col_ws'    , M.COL_MWS[:])
        m.h_cmnt    = m.stores.get(m.subset+'cmnt_heght', M.CMNT_MHT)
        m.sort      = m.stores.get(m.subset+'sort'      , (-1, True))   # Def sort is no sort
        m.cond_hl   = [s for s in m.stores.get(m.subset+'h.cond', []) if s]
        m.cond_s      = ''
        
        m.lexr      = m.stores.get(m.subset+'lxr'       , ed.get_prop(app.PROP_LEXER_CARET))
        m.all_ops   = 0==1      # Show also options without definition
        m.opts_defn = {}        # Meta-info for options: format, comment, dict of values, chapter, tags
        m.opts_full = {}        # Show all options
        # Cache
        m.SKWULs    = []        # Last filtered+sorted
        m.cols      = []        # Last info about listview columns
        m.itms      = []        # Last info about listview cells
        
        m.bk_files  = {}
#       m.do_file('backup-user')    if m.bk_sets else 0
        m.do_file('load-data')
        
        m.in_lexr   = False
        m.cur_in    = 0
        m.cur_op    = list(m.opts_full.keys())[0]
#       m.cur_op    = ''        # Name of current option
       #def __init__
    
    def do_file(self, what, data='', opts={}):
        M,m,d   = OptEdD,self,dict
        if False:pass
        elif what=='load-data':
            pass;              #LOG and log('',)
            m.opts_defn = parse_definitions(m.defn_path)
#           pass;               LOG and log('m.opts_defn={}',pf([o for o in m.opts_defn]))
            pass;              #LOG and log('m.opts_defn={}',pf([o for o in m.opts_defn if '2s' in o['frm']]))
            m.opts_full = load_vals(m.opts_defn, 'lexer '+m.lexr+'.json', m.all_ops)
            pass;              #LOG and log('m.opts_full={}',pf(m.opts_full))
        
        elif what=='set-dfns':
            m.defn_path = data
            m.do_file('load-data')
            return d(ctrls=odict(m.get_cnts('lvls')))
        
        elif what=='set-lexr':
            m.opts_full = load_vals(m.opts_defn, 'lexer '+m.lexr+'.json', m.all_ops)
            return d(ctrls=odict(m.get_cnts('lvls')))

        elif what=='out-rprt':
            if do_report(HTM_RPT_FILE, 'lexer '+m.lexr+'.json'):
                webbrowser.open_new_tab('file://'         +HTM_RPT_FILE)
                app.msg_status('Opened browser with file '+HTM_RPT_FILE)

        return []
       #def do_file
    
    def _prep_opt(self, opts='', ind=-1, nm=None):
        """ Prepare vars to show info about current option by 
                m.cur_op
                m.lexr
            Return
                {}  vi-attrs
                {}  en-attrs
                {}  val-attrs
                {}  items-attrs
        """
        M,m,d   = OptEdD,self,dict
        if opts=='key2ind':
            opt_nm  = nm if nm else m.cur_op
            m.cur_in= index_1([m.SKWULs[row][1] for row in range(len(m.SKWULs))], opt_nm, -1)
            return m.cur_in
        
        if opts=='ind2key':
            opt_in  = ind if -1!=ind else m.ag.cval('lvls')
            m.cur_op= m.SKWULs[opt_in][1] if -1<opt_in<len(m.SKWULs) else ''
            return m.cur_op
        
        if opts=='fid4ed':
            if not m.cur_op:    return 'lvls'
            frm     = m.opts_full[m.cur_op]['frm']
            return  'eded'  if frm in ('str', 'int', 'float', 'json')   else \
                    'edcb'  if frm in ('int2s', 'str2s')                else \
                    'edrf'  if frm in ('bool',)                         else \
                    'brow'  if frm in ('hotk', 'file')                  else \
                    'lvls'
        
        pass;                  #LOG and log('m.cur_op, m.lexr={}',(m.cur_op, m.lexr))
        vis,ens,vas,its = {},{},{},{}
        
#       vis['edlx'] = bool(m.lexr)
        ens['eded'] = ens['setd']                                       = False # All un=F
#       ens['eded'] = ens['setv']=ens['setd']                                       = False # All un=F
#       ens['eded'] = ens['setv']=ens['setd']=ens['edlx']                           = False # All un=F
        vis['eded'] = vis['edcb']=vis['edrf']=vis['edrt']=vis['brow']   = False # All vi=F
#       vis['eded'] = vis['setv']=vis['edcb']=vis['edrf']=vis['edrt']=vis['brow']   = False # All vi=F
        vas['eded'] = vas['dfvl']=vas['cmnt']= ''                                           # All ed empty
        vas['edcb'] = -1
        vas['edrf'] = vas['edrt'] = False
        its['edcb'] = []
        if not m.cur_op:
            # No current option
            vis['eded']     = True
           #vis['setv']     = True
        else:
            # Current option
            oi              = m.opts_full[m.cur_op]
            pass;              #LOG and log('oi={}',(oi))
            vas['dfvl']     = str(oi.get('jdf' , '')).replace('True', 'true').replace('False', 'false')
#           vas['dfvl']     = str(oi.get('def' , '')).replace('True', 'true').replace('False', 'false')
            vas['uval']     = oi.get('uval', '')
            vas['lval']     = oi.get('lval', '')
            vas['cmnt']     = oi.get('cmt' , '')
            frm             = oi['frm']
            ulvl_va         = vas['lval'] \
                                if m.in_lexr else \
                              vas['uval']                       # Cur val with cur state of "For lexer"
            ens['eded']     = frm not in ('json', 'hotk', 'file')
#           ens['edlx']     = True
           #ens['setv']     = frm not in ('json',)
            ens['setd']     = frm not in ('json',) and ulvl_va is not None
            if False:pass
            elif frm in ('str', 'int', 'float', 'json'):
                vis['eded'] = True
               #vis['setv'] = True
                vas['eded'] = str(ulvl_va)
            elif frm in ('hotk', 'file'):
                vis['eded'] = True
                vis['brow'] = True
                vas['eded'] = str(ulvl_va)
            elif frm in ('bool',):
                vis['edrf'] = True
                vis['edrt'] = True
                vas['edrf'] = ulvl_va==False
                vas['edrt'] = ulvl_va==True
            elif frm in ('font',):
                vis['edcb'] = True
                ens['edcb'] = True
                its['edcb'] = M.FONT_L
                vas['edcb'] = index_1(its['edcb'], ulvl_va, -1)
            elif frm in ('int2s', 'str2s'):
                vis['edcb'] = True
                ens['edcb'] = True
                its['edcb'] = oi['jdc']
                vas['edcb'] = index_1([k for (k,v) in oi['dct']], ulvl_va, -1)
            elif frm in ('strs',):
                vis['edcb'] = True
                ens['edcb'] = True
                its['edcb'] = oi['lst']
                vas['edcb'] = index_1(oi['lst'], ulvl_va, -1)
        
        pass;                  #LOG and log('ulvl_va={}',(ulvl_va))
        pass;                  #LOG and log('vis={}',(vis))
        pass;                  #LOG and log('ens={}',(ens))
        pass;                  #LOG and log('vas={}',(vas))
        pass;                  #LOG and log('its={}',(its))
        return vis,ens,vas,its
       #def _prep_opt

    def show(self
        , title                     # For cap of dlg
        ):
        M,m,d   = OptEdD,self,dict
#       pass;                   return

        def when_exit(ag):
            pass;              #LOG and log('',())
            pass;              #pr_   = dlg_proc_wpr(ag.id_dlg, app.DLG_CTL_PROP_GET, name='edch')
            pass;              #log('exit,pr_={}',('edch', {k:v for k,v in pr_.items() if k in ('x','y')}))
            pass;              #log('cols={}',(ag.cattr('lvls', 'cols')))
            m.col_ws= [ci['wd'] for ci in ag.cattr('lvls', 'cols')]
            m.stores[m.subset+'cmnt_heght'] = m.ag.cattr('cmnt', 'h')
           #def when_exit

        m.pre_cnts()
        m.ag = DlgAgent(
            form =dict(cap     = title + f(' ({})', VERSION_V)
                      ,resize  = True
                      ,w       = m.dlg_w    ,w_min=m.dlg_min_w
                      ,h       = m.dlg_h
                      ,on_resize=m.do_resize
                      )
        ,   ctrls=m.get_cnts()
        ,   vals =m.get_vals()
        ,   fid  ='cond'
                                ,options = {
                                    'gen_repro_to_file':'repro_dlg_opted.py'    #NOTE: repro
                                }
        )
        m.ag.show(when_exit)
        m.ag    = None

        # Save for next using
        m.stores[m.subset+'col_ws']     = m.col_ws
        m.stores[m.subset+'sort']       = m.sort
        m.stores[m.subset+'h.cond']     = m.cond_hl
        open(CFG_JSON, 'w').write(json.dumps(m.stores, indent=4))
       #def show
    
    def pre_cnts(self):
        M,m         = OptEdD,self
        m.dlg_min_w = 10 + sum(M.COL_MWS) + M.COL_N + M.SCROLL_W
        m.dlg_w     = 10 + sum(m.col_ws)  + M.COL_N + M.SCROLL_W
#       m.dlg_min_w = 10 + sum(M.COL_MWS) +                   M.SCROLL_W
#       m.dlg_w     = 10 + sum(m.col_ws)  +                   M.SCROLL_W
        m.dlg_h     = 270 + m.h_cmnt    +10
#       pass;                   self.dlg_h  = 25
       #def pre_cnts
    
    def get_cnts(self, what=''):
        M,m,d   = OptEdD,self,dict
        
        reNotWdChar = re.compile(r'\W')
        def test_fltr(fltr_s, op, oi):
            if not fltr_s:                                  return True
            pass;              #LOG and log('fltr_s, op, oi[!]={}',(fltr_s, op, oi['!']))
            if '!!' in fltr_s and '!!' not in oi['!']:      return False
            pass;              #LOG and log('skip !!',())
            if  '!' in fltr_s and  '!' not in oi['!']:      return False
            pass;              #LOG and log('skip !',())
            text    = op \
                    + (' '+oi.get('cmt', '') if '#' in fltr_s else '')
            text    = text.upper()
            fltr_s  = fltr_s.replace('!', '').replace('#', '').upper()
            if '<' in fltr_s or '>' in fltr_s:
                text    = '·' + reNotWdChar.sub('·', text)    + '·'
                fltr_s  = ' ' + fltr_s + ' '
                fltr_s  = fltr_s.replace(' <', ' ·').replace('> ', '· ')
            pass;              #LOG and log('fltr_s, text={}',(fltr_s, text))
#           return any(map(lambda c:c in text, fltr_s.split()))
            return all(map(lambda c:c in text, fltr_s.split()))
           #def test_fltr

        def get_tbl_cols(opts_full, SKWULs, sort, col_ws):
            stat_o  = f(' ({}/{})', len(SKWULs), len(opts_full))
            sort_cs = ['' if c!=sort[0] else '↑ ' if sort[1] else '↓ ' for c in range(6)] # ▲ ▼ ?
            cols    = [  d(nm=sort_cs[0]+M.COL_NMS[0]       ,wd=col_ws[0] ,mi=M.COL_MWS[0])
                        ,d(nm=sort_cs[1]+M.COL_NMS[1]+stat_o,wd=col_ws[1] ,mi=M.COL_MWS[1])
                        ,d(nm=sort_cs[2]+M.COL_NMS[2]       ,wd=col_ws[2] ,mi=M.COL_MWS[2]   ,al='C')
                        ,d(nm=sort_cs[3]+M.COL_NMS[3]       ,wd=col_ws[3] ,mi=M.COL_MWS[3])
                        ,d(nm=sort_cs[4]+M.COL_NMS[4]       ,wd=col_ws[4] ,mi=M.COL_MWS[4])
                        ,d(nm=sort_cs[5]+M.COL_NMS[5]       ,wd=col_ws[5] ,mi=M.COL_MWS[5])
                        ]
            return cols
           #def get_tbl_cols
        
        def get_tbl_data(opts_full, cond_s, sort, col_ws):
            # Filter table data
            pass;              #LOG and log('cond_s={}',(cond_s))
            chp_cond    = ''
            if  '@' in cond_s:
                # Prepare to match chapters
                chp_cond    = ' '.join([mt.group(1) for mt in re.finditer(r'@(\w*)'    , cond_s)]).upper()
                cond_s      =                                 re.sub(     r'@(\w*)', '', cond_s)
            pass;              #LOG and log('chp_cond, cond_s={}',(chp_cond, cond_s))
            SKWULs  = [  (oi.get('chp','') 
                         ,op
                         ,oi['!']
                         ,str(oi.get('jdf' ,'')).replace('True', 'true').replace('False', 'false')
                         ,str(oi.get('juvl','')).replace('True', 'true').replace('False', 'false')
                         ,str(oi.get('jlvl','')).replace('True', 'true').replace('False', 'false')
                         ,oi['frm']
                         )
                            for op,oi in opts_full.items()
                            if  (not chp_cond   or chp_cond in oi['chp'].upper())
                            and (not cond_s     or test_fltr(cond_s, op, oi))
                      ]
            # Sort table data
#           sort_cs = ['' if c!=sort[0] else '↑ ' if sort[1] else '↓ ' for c in range(6)] # ▲ ▼ ?
            if -1 != sort[0]:     # With sort col
                SKWULs      = sorted(SKWULs
                               ,key=lambda it:('_'                                  # Replace '' to '_'
                                        if not it[sort[0]] and not sort[1] else     #  if need sort
                                               it[sort[0]])                         # to show empties in bottom
                               ,reverse=sort[1])
            # Fill table
#           stat_o  = f(' ({}/{})', len(SKWULs), len(opts_full))
            pass;              #LOG and log('M.COL_NMS,sort_cs,col_ws,M.COL_MWS={}',(len(M.COL_NMS),len(sort_cs),len(col_ws),len(M.COL_MWS)))
            cols    = get_tbl_cols(opts_full, SKWULs, sort, col_ws)
#           cols    = [  d(nm=sort_cs[0]+M.COL_NMS[0]       ,wd=col_ws[0] ,mi=M.COL_MWS[0])
#                       ,d(nm=sort_cs[1]+M.COL_NMS[1]+stat_o,wd=col_ws[1] ,mi=M.COL_MWS[1])
#                       ,d(nm=sort_cs[2]+M.COL_NMS[2]       ,wd=col_ws[2] ,mi=M.COL_MWS[2]   ,al='C')
#                       ,d(nm=sort_cs[3]+M.COL_NMS[3]       ,wd=col_ws[3] ,mi=M.COL_MWS[3])
#                       ,d(nm=sort_cs[4]+M.COL_NMS[4]       ,wd=col_ws[4] ,mi=M.COL_MWS[4])
#                       ,d(nm=sort_cs[5]+M.COL_NMS[5]       ,wd=col_ws[5] ,mi=M.COL_MWS[5])
#                       ]
            itms    = (list(zip([_('Section'),_('Option'), '', _('Default'), _('In user'), _('In lexer')], map(str, col_ws)))
                     #,         [ (sc+' '+fm    ,k         ,w    ,dv           ,uv           ,lv)    # for debug
                      ,         [ (sc           ,k         ,w    ,dv           ,uv           ,lv)    # for user
                        for  (     sc           ,k         ,w    ,dv           ,uv           ,lv, fm) in SKWULs ]
                      )
            return SKWULs, cols, itms
           #def get_tbl_data
           
        if not what or '+lvls' in what:
            m.SKWULs,\
            m.cols  ,\
            m.itms  = get_tbl_data(m.opts_full, m.cond_s, m.sort, m.col_ws)

        if '+cols' in what:
            pass;              #LOG and log('m.col_ws={}',(m.col_ws))
            m.cols  = get_tbl_cols(m.opts_full, m.SKWULs, m.sort, m.col_ws)
            pass;              #LOG and log('m.cols={}',(m.cols))
        
        # Prepare [Def]Val data by m.cur_op
        vis,ens,vas,its = m._prep_opt()
        
        cnts    = []
        if '+cond' in what:
            cnts   += [0
            ,('cond',d(items=m.cond_hl))
            ][1:]

        if '+cols' in what or '=cols' in what:
            cnts   += [0
            ,('lvls',d(cols=m.cols))
            ][1:]
        if '+lvls' in what or '=lvls' in what:
            cnts   += [0
            ,('lvls',d(cols=m.cols, items=m.itms))
            ][1:]

        if '+cur' in what:
            cnts   += [0
            ,('eded',d(vis=vis['eded'],en=ens['eded']                   ))
            ,('edcb',d(vis=vis['edcb']               ,items=its['edcb'] ))
            ,('edrf',d(vis=vis['edrf']                                  ))
            ,('edrt',d(vis=vis['edrt']                                  ))
            ,('brow',d(vis=vis['brow']                                  ))
           #,('setv',d(vis=vis['setv'],en=ens['setv']                   ))
#           ,('edlx',d(vis=vis['edlx']                                  ))
#           ,('edlx',d(vis=vis['edlx'],en=ens['edlx']                   ))
            ,('setd',d(                en=ens['setd']                   ))
            ][1:]

        if what and cnts:
            # Part info
            return cnts

        # Full dlg controls info    #NOTE: cnts
        cmnt_t  = m.dlg_h-m.h_cmnt-5
        cnts    = [0                                                                                                #
    # Hidden buttons                                                                                                                     
 ,('flt-',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&l'               ,sto=False                                  ))  # &l
 ,('fltr',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap=''                 ,sto=False  ,def_bt='1'                     ))  # Enter
 ,('srt0',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&1'               ,sto=False                                  ))  # &1
 ,('srt1',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&2'               ,sto=False                                  ))  # &2
 ,('srt2',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&3'               ,sto=False                                  ))  # &3
 ,('srt3',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&4'               ,sto=False                                  ))  # &4
 ,('srt4',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&5'               ,sto=False                                  ))  # &5
 ,('srt5',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&6'               ,sto=False                                  ))  # &6
 ,('cws-',d(tp='bt' ,t=0        ,l=000          ,w=000      ,cap='&W'               ,sto=False                                  ))  # &w
 ,('help',d(tp='bt' ,t=0        ,l=0            ,w=0        ,cap='&H'               ,sto=False                                  ))  # &h
    # Top-panel                                                                                                                      
 ,('ptop',d(tp='pn' ,h=    270 ,w=m.dlg_w                   ,ali=ALI_CL
                    ,h_min=270                                                                                                          ))
    # Menu                                                                                                                      
 ,('menu',d(tp='bt' ,tid='cond' ,l=m.dlg_w-25-5 ,w=25       ,p='ptop'   ,cap='&+'                                              ,a='LR'  ))  # &+
    # Filter                                                                                                                            
 ,('flt_',d(tp='lb' ,tid='cond' ,l=  5          ,w= 60      ,p='ptop'   ,cap=_('>&Filter:')     ,hint=M.FLTR_H                          ))  # &f
 ,('cond',d(tp='cb' ,t=  5      ,l= 70          ,w=200      ,p='ptop'   ,items=m.cond_hl                                                ))  #
    # Table of keys+values                                                                                                              
 ,('lvls',d(tp='lvw',t=35       ,l=5 ,h=160     ,r=m.dlg_w-5,p='ptop'   ,items=m.itms,cols=m.cols   ,grid='1'                  ,a='tBlR'))  #
    # Editors for value                                                                                                                 
 ,('ed__',d(tp='lb' ,t=210      ,l=  5          ,w=110      ,p='ptop'   ,cap=_('>&Value:')                                     ,a='TB'  ))  # &v 
 ,('eded',d(tp='ed' ,tid='ed__' ,l=120  ,r=m.dlg_w-220      ,p='ptop'                           ,vis=vis['eded'],en=ens['eded'],a='TBlR'))  #
 ,('edcb',d(tp='cbr',tid='ed__' ,l=120  ,r=m.dlg_w-220      ,p='ptop'   ,items=its['edcb']      ,vis=vis['edcb']               ,a='TBlR'))  #
 ,('edrf',d(tp='rd' ,tid='ed__' ,l=120          ,w= 60      ,p='ptop'   ,cap=_('f&alse')        ,vis=vis['edrf']               ,a='TB'  ))  # &a
 ,('edrt',d(tp='rd' ,tid='ed__' ,l=180          ,w= 60      ,p='ptop'   ,cap=_('tru&e')         ,vis=vis['edrt']               ,a='TB'  ))  # &e
 ,('brow',d(tp='bt' ,tid='ed__' ,l=m.dlg_w-220  ,w= 70      ,p='ptop'   ,cap=_('&...')          ,vis=vis['brow']               ,a='TBLR'))  # &.
    # View def-value                                                                                                                    
 ,('dfv_',d(tp='lb' ,tid='dfvl' ,l=  5          ,w=110      ,p='ptop'   ,cap=_('>Default val&ue:')                             ,a='TB'  ))  # &u
 ,('dfvl',d(tp='ed' ,t=235      ,l=120  ,r=m.dlg_w-220      ,p='ptop'   ,ro_mono_brd='1,0,1'                                   ,a='TBlR'))  #
 ,('setd',d(tp='bt' ,tid='dfvl' ,l=m.dlg_w-220  ,w= 70      ,p='ptop'   ,cap=_('Rese&t')                        ,en=ens['setd'],a='TBLR'))  # &t
    # For lexer                                                                                                                         
 ,('edlx',d(tp='ch' ,tid='ed__' ,l=m.dlg_w-125  ,w= 90      ,p='ptop'   ,cap=_('For Le&xer')                                   ,a='TBLR'))  # &x
 ,('lexr',d(tp='cbr',tid='dfvl' ,l=m.dlg_w-125  ,w=120      ,p='ptop'   ,items=m.lexr_w_l                                      ,a='TBLR'))
    # Comment                                                                                                                           
 ,('cmnt',d(tp='me' ,t=cmnt_t   ,h=    m.h_cmnt 
                                ,h_min=M.CMNT_MHT           ,ali=ALI_BT,sp_lrb=5       ,ro_mono_brd='1,1,1'    ))  # &h
 ,('cmsp',d(tp='sp' ,y=cmnt_t-5                             ,ali=ALI_BT,sp_lr=5                                      ))
                ][1:]
        cnts    = odict(cnts)
        cnts['menu']['call']            = m.do_menu
        cnts['flt-']['call']            = m.do_fltr
        cnts['fltr']['call']            = m.do_fltr
#       cnts['cond']['call']            = m.do_fltr
        cnts['lexr']['call']            = m.do_lexr
        cnts['edlx']['call']            = m.do_lexr
        cnts['lvls']['call']            = m.do_sele
        cnts['lvls']['on_click_header'] = m.do_sort
        cnts['srt0']['call']            = m.do_sort
        cnts['srt1']['call']            = m.do_sort
        cnts['srt2']['call']            = m.do_sort
        cnts['srt3']['call']            = m.do_sort
        cnts['srt4']['call']            = m.do_sort
        cnts['cmsp']['call']            = m.do_cust
        cnts['cws-']['call']            = m.do_cust
#       cnts['lvls']['on_click']        = m.do_setv   #lambda idd,idc,data:print('on dbl d=', data)
        cnts['lvls']['on_click_dbl']    = m.do_dbcl   #lambda idd,idc,data:print('on dbl d=', data)
        cnts['setd']['call']            = m.do_setv
        cnts['edcb']['call']            = m.do_setv
        cnts['edrf']['call']            = m.do_setv
        cnts['edrt']['call']            = m.do_setv
        cnts['brow']['call']            = m.do_setv
#       cnts['setv']['call']            = m.do_setv
        cnts['help']['call']            = m.do_help
        return cnts
       #def get_cnts
    
    def get_vals(self, what=''):
        M,m,d   = OptEdD,self,dict
        m.cur_in    = m._prep_opt('key2ind')
        if not what or 'cur' in what:
            vis,ens,vas,its = m._prep_opt()
        if not what:
            # all
            return dict(lvls=m.cur_in
                       ,eded=vas['eded']
                       ,edcb=vas['edcb']
                       ,edrf=vas['edrf']
                       ,edrt=vas['edrt']
                       ,dfvl=vas['dfvl']
                       ,cmnt=vas['cmnt']
                       ,edlx=m.in_lexr
                       ,lexr=m.lexr_l.index(m.lexr)     if m.lexr in m.lexr_l else -1
                       )
        if '+' in what:
            rsp = dict()
            if '+lvls' in what:
                rsp.update(dict(
                        lvls=m.cur_in
                        ))
            if '+cur' in what:
                rsp.update(dict(
                        eded=vas['eded']
                       ,edcb=vas['edcb']
                       ,edrf=vas['edrf']
                       ,edrt=vas['edrt']
                       ,dfvl=vas['dfvl']
                       ,cmnt=vas['cmnt']
                       ))
            if '+inlx' in what:
                rsp.update(dict(
                        edlx=m.in_lexr
                        ))
            pass;              #LOG and log('rsp={}',(rsp))
            return rsp
                    
        if what=='lvls':
            return dict(lvls=m.cur_in
                       )
        if what=='lvls-cur':
            return dict(lvls=m.cur_in
                       ,eded=vas['eded']
                       ,edcb=vas['edcb']
                       ,edrf=vas['edrf']
                       ,edrt=vas['edrt']
                       ,dfvl=vas['dfvl']
                       ,cmnt=vas['cmnt']
                       )
        if what=='cur':
            return dict(eded=vas['eded']
                       ,edcb=vas['edcb']
                       ,edrf=vas['edrf']
                       ,edrt=vas['edrt']
                       ,dfvl=vas['dfvl']
                       ,cmnt=vas['cmnt']
                       )
       #def get_vals
    
    def do_resize(self, ag):
        M,m,d   = OptEdD,self,dict
        f_w     = ag.fattr('w')
        l_w     = ag.cattr('lvls', 'w')
        pass;                  #LOG and log('f_w,l_w={}',(f_w,l_w))
        if f_w < m.dlg_min_w:           return []   # fake event
        
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
        if f_w == m.dlg_min_w and m.col_ws!=M.COL_MWS:
            return m.do_cust('cws-', ag)

        sum_ws  = sum(m.col_ws)
        pass;                  #LOG and log('l_w,sum_ws={}',(l_w,sum_ws))
        if sum_ws >= (l_w - M.COL_N - M.SCROLL_W):return []   # decrease dlg - need user choice
        
        # Auto increase widths of def-val and user-val cols
        extra   = int((l_w - M.COL_N - M.SCROLL_W - sum_ws)/2)
        pass;                  #LOG and log('extra={}',(extra))
        pass;                  #LOG and log('m.col_ws={}',(m.col_ws))
        m.col_ws[3] += extra
        m.col_ws[4] += extra
        pass;                  #LOG and log('m.col_ws={}',(m.col_ws))
        return d(ctrls=m.get_cnts('+cols'))
       #def do_resize
    
    def do_cust(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        pass;                  #LOG and log('aid={}',(aid))
        if False:pass
        elif aid=='cmsp':
            # Splitter moved
            sp_y    = ag.cattr('cmsp', 'y')
            return []
            ##??
            
        elif aid=='cws-':
            # Set def col widths
            m.col_ws    = M.COL_MWS[:]
            m.stores.pop(m.subset+'col_ws', None)
            return d(ctrls=m.get_cnts('+cols'))
       #def do_cust
    
    def do_menu(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
        if scam=='c' and aid=='menu':
            return dlg_valign_consts()

        def wnen_menu(ag, tag):
            pass;              #LOG and log('tag={}',(tag))
            if False:pass
            elif tag=='srt-':
                return m.do_sort('', ag, -1)
            elif tag[:3]=='srt':
                return m.do_sort('', ag, int(tag[3]))
            
#           elif tag=='hcmt':
#               h_cmnt_s    = app.dlg_input(f(_('Height of the Comment (min={})'), M.CMNT_MHT), str(m.h_cmnt))
#               if h_cmnt_s is None or not re.match(r'\d+', h_cmnt_s):   return []
#               m.h_cmnt    = max(int(h_cmnt_s), M.CMNT_MHT)
#               m.stores[m.subset+'cmnt_heght'] = m.h_cmnt
#               return []
            
            elif tag=='cws-':
                return m.do_cust(tag, ag)
#               m.col_ws    = M.COL_MWS[:]
#               m.stores.pop(m.subset+'col_ws', None)
#               return d(ctrls=odict(m.get_cnts('+lvls')))
            
#           elif tag=='lubk':
#               if app.ID_OK != app.msg_box(
#                               _('Restore user settings from backup copy?')
#                               , app.MB_OKCANCEL+app.MB_ICONQUESTION): return []
#               return m.do_file('restore-user')
#           elif tag=='llbk':
#               if app.ID_OK != app.msg_box(
#                               f(_('Restore lexer "{}" settings from backup copy?'), m.lexr)
#                               , app.MB_OKCANCEL+app.MB_ICONQUESTION): return []
#               return m.do_file('restore-lexr')
#           elif tag=='dobk':
#               m.stores[m.subset+'bk_sets'] = m.bk_sets = not m.bk_sets
#               return []
            
            elif tag=='dfns':
                m.col_ws    = [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
                new_file    = app.dlg_file(True, m.defn_path.name, str(m.defn_path.parent), 'JSONs|*.json')
                if not new_file or not os.path.isfile(new_file):    return []
                return m.do_file('set-dfns', new_file)
            elif tag=='full':
                m.col_ws    = [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
                m.all_ops   = not m.all_ops
                m.opts_full = load_vals(m.opts_defn, 'lexer '+m.lexr+'.json', m.all_ops)
                return d(ctrls=odict(m.get_cnts('+lvls')))
            
            elif tag=='rprt':
                m.do_file('out-rprt')
            elif tag=='help':
                return m.do_help('', ag)
            return []
        pass;                  #LOG and log('',())
        mn_its  = [0
            ,d(                 cap=_('File') ,sub=[0
                ,d( tag='rprt', cap=_('Create HTML report about all options')               ,cmd=wnen_menu)
                ,d(             cap='-')
                ,d( tag='full', cap=_('Show all options for user and lexer'),ch=m.all_ops   ,cmd=wnen_menu)
                ,d( tag='dfns', cap=_('Choose file with definitions of options...')         ,cmd=wnen_menu)
#               ,d(             cap='-')
#               ,d( tag='dobk', cap=_('Create backup copy of user/lexer settings')  
#                                                                       ,ch=m.bk_sets       ,cmd=wnen_menu)
#               ,d( tag='lubk', cap=_('Restore user settings...')
#                                                                   ,en=      bool(m.bk_files.get('user',''))
#                                                                                           ,cmd=wnen_menu)
#               ,d( tag='llbk', cap=f(_('Restore lexer "{}" settings...'), m.lexr)
#                                                                   ,en=m.lexr and m.bk_files.get(m.lexr,'')
#                                                                                           ,cmd=wnen_menu)
                ][1:])
            ,d(                 cap=_('Sorting') ,sub=[
                 d( tag='srt'+str(cn), cap=f(_('By column "{}"'), cs)   ,ch=m.sort[0]==cn   ,key='Alt+'+str(1+cn)
                                                                                            ,cmd=wnen_menu)
                 for cn, cs in enumerate(M.COL_NMS)
                ]+[0
                ,d(             cap='-')
                ,d( tag='srt-', cap=_('Clear sorting')  ,en=(m.sort[0]!=-1)                 ,cmd=wnen_menu)
                ][1:])
            ,d(                 cap=_('Fit dialog') ,sub=[0
#               ,d( tag='hcmt', cap=_('Set comment height (need restart)...')               ,cmd=wnen_menu)
                ,d( tag='cws-', cap=_('Set default columns widths')         ,key='Alt+W'    ,cmd=wnen_menu)
                ][1:])
            ,d(                 cap='-')
            ,d(     tag='help', cap=_('Help...')                            ,key='Alt+H'    ,cmd=wnen_menu)
            ][1:]
        ag.show_menu(aid,mn_its)
        return []
       #def do_menu

    def do_fltr(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
        fid     = ag.fattr('fid')
        pass;                   LOG and log('aid,fid={}',(aid,fid))
        if aid=='fltr' and fid in ('dfvl', 'eded', 'edrf', 'edrt'):
            # Imitate default button
            return m.do_setv('setd' if fid in ('dfvl',)         else
                             'setv' if fid in ('eded',)         else
                             fid    if fid in ('edrf', 'edrt')  else
                             ''
                            , ag)
            
        if aid=='cond':
            pass;              #LOG and log('ag.cval(cond)={}',(ag.cval('cond')))
            m.cond_s    = ag.cval('cond')
        if aid=='fltr':
            m.cond_s    = ag.cval('cond')
            m.cond_hl   = add_to_history(m.cond_s, m.cond_hl, MAX_HIST, unicase=False)  if m.cond_s else m.cond_hl
        if aid=='flt-':
            m.cond_s    = ''
        # Select old/new op
        m.cur_op= m._prep_opt('ind2key')
        ctrls   = m.get_cnts('+lvls')
        m.cur_in= m._prep_opt('key2ind')
        if m.cur_in<0 and m.SKWULs:
            # Sel top if old hidden
            m.cur_in= 0
            m.cur_op= m._prep_opt('ind2key', ind=m.cur_in)
        return d(ctrls=m.get_cnts('+cond =lvls +cur')
                ,vals =m.get_vals()
                )
               
       #def do_fltr
    
    def do_sort(self, aid, ag, col=-1):
        pass;                  #LOG and log('col={}',(col))
        pass;                  #return []
        M,m,d   = OptEdD,self,dict
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
        
        col     = int(aid[3]) if aid[:3]=='srt' else col
        col_pre = m.sort[0]
        m.sort  = (-1 , True)       if col    ==-1                      else  \
                  (col, False)      if col_pre==-1                      else  \
                  (col, False)      if col_pre!=col                     else  \
                  (col, True)       if col_pre==col and not m.sort[1]   else  \
                  (-1 , True)
        old_in  = m._prep_opt('key2ind')
        ctrls   = m.get_cnts('+lvls')
        if old_in==0:
            # Set top if old was top
            m.cur_in= 0
            m.cur_op= m._prep_opt('ind2key', ind=m.cur_in)
        else:
            # Save old op
            m.cur_in= m._prep_opt('key2ind')
        return d(ctrls=m.get_cnts('=lvls +cur')
                ,vals =m.get_vals()
                )
       #def do_sort

    def do_sele(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        pass;                  #LOG and log('',())
        m.cur_op= m._prep_opt('ind2key')
        return d(ctrls=odict(m.get_cnts('+cur'))
                ,vals =      m.get_vals('cur')
                )
       #def do_sele
    
    def do_lexr(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        pass;                  #LOG and log('aid={}',(aid))
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]

        if False:pass
        elif aid=='edlx':
            # Changed "In lexer"
            m.in_lexr   = ag.cval('edlx')
            return d(ctrls=m.get_cnts('+cur')
                    ,vals =m.get_vals('cur')
                    ,form =d(fid=m._prep_opt('fid4ed'))
#           return d(vals =m.get_vals('cur')
                    )
        elif aid=='lexr':
            # Changed "For lexer"
            lexr_n  = ag.cval('lexr')
            m.lexr  = m.lexr_l[lexr_n]      if lexr_n>=0 else ''
            m.cur_op= m._prep_opt('ind2key')
            m.do_file('load-data')
            m.cur_in= m._prep_opt('key2ind')
            return d(ctrls=m.get_cnts()
                    ,vals =m.get_vals()
                    )
       #def do_lexr
    
    def do_dbcl(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        pass;                  #LOG and log('data={}',(data))
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]

        if aid!='lvls':     return []
        # Dbl-click on lvls cell
        if sum(m.col_ws) > ag.cattr('lvls', 'w') - M.SCROLL_W:
            # Has hor-scrolling
            pass;              #LOG and log('skip as h-scroll',())
            return []
        op_r    = ag.cval('lvls')
        op_c    = next(filter(                              # next(filter())==first_true
                    lambda col_n_sw: col_n_sw[1]>data[0]    # > x from click (x,y)
                  , enumerate(accumulate(m.col_ws))         # (n_col, sum(col<=n))
                  ), [-1, -1
                  ])[0]
        pass;                  #LOG and log('op_r,op_c={}',(op_r,op_c))
        if False:pass
        elif -1==op_r:
            pass;              #LOG and log('skip as no opt',())
        elif -1==op_c:
            pass;              #LOG and log('skip as miss col',())
        elif 4==op_c and     m.in_lexr:
            # Switch to user vals
            m.in_lexr   = False
        elif 5==op_c and not m.in_lexr:
            # Switch to lexer vals
            m.in_lexr   = True
        return d(ctrls=m.get_cnts('+cur')
                ,vals =m.get_vals('+cur+inlx')
                ,form =d(fid=m._prep_opt('fid4ed'))
                )
       #def do_dbcl
    
    def do_setv(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        pass;                  #LOG and log('aid,m.cur_op={}',(aid,m.cur_op))
        if not m.cur_op:   return []
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
        
        trg = 'lexer '+m.lexr+'.json' if m.in_lexr else 'user.join'
        op  = m.cur_op
        oi  = m.opts_full[m.cur_op]
        frm = oi['frm']
        if frm=='json':
            app.msg_status(f(_('Edit {} to change value'), trg))
            return []
        dval= oi.get('def', '')
        uval= oi.get('uval', '')
        lval= oi.get('lval', '')
        ulvl= lval if m.in_lexr else uval
        newv= None
        if False:pass
        elif aid=='lvls':
            # Dbl-click
            if sum(m.col_ws) > ag.cattr('lvls', 'w') - M.SCROLL_W:
                # Has hor-scrolling
                pass;           LOG and log('skip as h-scroll',())
                return []
            pass;              #LOG and log('data={}',(data))
            op_r    = ag.cval('lvls')
            op_c    = next(filter(                              # next(filter())==first_true
                        lambda col_n_sw: col_n_sw[1]>data[0]    # > x from click (x,y)
                      , enumerate(accumulate(m.col_ws))         # (n_col, sum(col<=n))
                      ), [-1, -1
                      ])[0]
            pass;               LOG and log('op_r,op_c={}',(op_r,op_c))
            if -1==op_c:
                pass;           LOG and log('skip as miss col',())
            return []
        elif aid=='setd':
            # Remove from user/lexer
            newv= None
        
        elif aid=='brow' and frm=='hotk':
            app.msg_status_alt(f(_('Default value: "{}", Old value: "{}"'), dval, ulvl), 20)
            if frm=='hotk': # Choose Hotkey
                newv    = app.dlg_hotkey(op)
            if frm=='file': # Choose File
                newv    = app.dlg_file(True, '', os.path.expanduser(ulvl), '')
            app.msg_status_alt('', 0)
            if not newv:    return []
        
        elif aid in ('edcb', 'setv', 'edrf', 'edrt'):   # Add/Set opt into user/lexer
            vl_l    = [k for k,v in oi.get('dct', [])]  if 'dct' in oi else oi.get('lst', [])
            newv    = vl_l[m.ag.cval('edcb')]   if aid=='edcb'  else \
                           m.ag.cval('eded')    if aid=='setv'  else \
                      False                     if aid=='edrf'  else \
                      True                      if aid=='edrt'  else \
                      None
            if aid=='setv':
                try:
                    newv    =   int(newv)   if frm=='int'   else \
                              float(newv)   if frm=='float' else \
                                    newv
                except Exception as ex:
                    app.msg_box(f(_('Uncorrect value. Need format: {}'), frm)
                               , app.MB_OK+app.MB_ICONWARNING)
                    return d(form=d(fid='eded'))
            if newv is None:    return []

        if newv == ulvl:    return []
        
        # Change target file
        apx.set_opt(op
                   ,newv
                   ,apx.CONFIG_LEV_LEX if m.in_lexr else apx.CONFIG_LEV_USER
                   ,ed_cfg  =None
                   ,lexer   =m.lexr
                   )
        
        # Change dlg data
        pass;                  #LOG and log('?? oi={}',(oi))
#       pass;                   LOG and log('?? m.opts_full={}',pf(m.opts_full))
        key4val = 'lval' if m.in_lexr else 'uval'
        if False:pass
        elif aid=='setd':
            oi.pop(key4val, None)
        else:
            pass;              #LOG and log('key4val, newv={}',(key4val, newv))
            oi[key4val] = newv
        upd_cald_vals(m.opts_full)
        pass;                  #LOG and log('ok oi={}',(oi))
#       pass;                   LOG and log('ok m.opts_full={}',pf(m.opts_full))
        
        return d(ctrls=m.get_cnts('+lvls')
                ,vals =m.get_vals('lvls-cur')
                )
       #def do_setv
    
    def do_help(self, aid, ag, data=''):
        M,m,d   = OptEdD,self,dict
        pass;                   LOG and log('',())
        dlg_wrapper('Help'
        ,   510, 410 
        ,   [d(cid='body', tp='me', l=5, t=5, w=500, h=400, ro_mono_brd='1,1,0')]
        ,   d(      body=   #NOTE: help
                 f(
  _(  'About "{fltr}"'
    '\r '
   )
   +M.FLTR_H+
  _('\r '
    '\rMore tips.'
    '\r • ENTER to apply filter and to change or reset value.'
    '\r • Double click on any cell in columns'
    '\r     "{c_usr}"'
    '\r     "{c_lxr}"'
    '\r   to switch "{in_lxr}".'
   )             , c_usr=M.COL_NMS[M.COL_USR]
                 , c_lxr=M.COL_NMS[M.COL_LXR]
                 , fltr = ag.cattr('flt_', 'cap', live=False).replace('&', '').strip(':')
                 , in_lxr=ag.cattr('edlx', 'cap', live=False).replace('&', '')
                 ))
        )
        return []
       #def do_help
    
   #class OptEdD


class Command:
    def dlg_cuda_options(self):
        if app.app_api_version()<MIN_API_VER_4AG: return app.msg_status(_('Need update CudaText'))
        pass;                  #LOG and log('ok',())
        pass;                  #dlg_opt_editor('CudaText options', '')
        pass;                  #return 
        OptEdD(
          keys_info=None
#       , path_raw_keys_info=apx.get_def_setting_dir()          +os.sep+'kv-default.json'
        , path_raw_keys_info=apx.get_def_setting_dir()          +os.sep+'default.json'
        , path_svd_keys_info=app.app_path(app.APP_DIR_SETTINGS) +os.sep+'_default_keys_info.json'
        , subset='df.'
        ).show('CudaText options')
       #def dlg_cuda_options

    def dlg_cuda_opts(self):
        pass;                  #LOG and log('ok',())
        pass;                  #dlg_opt_editor('CudaText options', '')
        pass;                  #return 
#       cuda_opts   = apx.get_def_setting_dir()+os.sep+'default_options.json'
#       cuda_opts   = os.path.dirname(__file__)+os.sep+'default_options.json'
#       dlg_opt_editor('CudaText options', json.loads(open(cuda_opts).read()))
        dlg_opt_editor('CudaText options'
        , keys_info=None
        , path_raw_keys_info=apx.get_def_setting_dir()          +os.sep+'default.json'
        , path_svd_keys_info=app.app_path(app.APP_DIR_SETTINGS) +os.sep+'_default_keys_info.json'
        , subset='def.'
        )
       #def dlg_cuda_opts
   #class Command

def dlg_opt_editor(title, keys_info=None
        , path_raw_keys_info=''
        , path_svd_keys_info=''
        , subset=''
        ):
    dlg_opt_editor_wr(title, keys_info, path_raw_keys_info, path_svd_keys_info, subset)
   #def dlg_opt_editor

def dlg_opt_editor_wr(title, keys_info=None
        , path_raw_keys_info=''
        , path_svd_keys_info=''
        , subset=''
        ):
    """ Editor for any json data.
        Params 
            title       (str)   Dialog title
            keys_info   (list)  Info for each key as dict
                                    key:    (str)
                                    format: (str)   bool|int|str|float|enum_i|enum_s|json
                                    comment:(str)
                                            (str list)
                                    def_val: 
                                    dct:    (dict)
                                            (pairs list)
    """
    if app.app_api_version()<MIN_API_VER_4WR: return app.msg_status(_('Need update CudaText'))
    if not keys_info:
        if not os.path.isfile(path_raw_keys_info):
            return app.msg_status(_('No sourse for key-info'))
        # If ready json exists - use ready
        # Else - parse raw (and save as ready)

        mtime_raw   = os.path.getmtime(path_raw_keys_info)
        mtime_svd   = os.path.getmtime(path_svd_keys_info) if os.path.exists(path_svd_keys_info) else 0
        if 'use ready'!='use ready' and mtime_raw < mtime_svd:
            # Use ready
            keys_info   = json.loads(open(path_svd_keys_info, encoding='utf8').read(), object_pairs_hook=odict)
            app.msg_status(f(_('Load key-info ({}) from "{}"'),len(keys_info),path_svd_keys_info))
        else:
            # Parse raw
            keys_info   = parse_raw_keys_info(path_raw_keys_info)
            if not keys_info:
                return app.msg_status(_('Bad sourse for key-info'))
            if path_svd_keys_info:
                # Save as ready
                open(path_svd_keys_info,'w').write(json.dumps(keys_info, indent=4))
                app.msg_status(_('Update key-info at '+path_svd_keys_info))
        pass;                  #return
            
#   if -1== 1:  # Test data
#       keys_info = [dict(key='key-bool',format='bool'  ,def_val=False           ,comment= 'smth')
#                   ,dict(key='key-int' ,format='int'   ,def_val=123             ,comment= 'smth\nsmth')
#                   ,dict(key='key-aint'                ,def_val=123             ,comment= 'smth\nsmth')
#                   ,dict(key='key-str' ,format='str'   ,def_val='xyz'           ,comment= 'smth')
#                   ,dict(key='key-flo' ,format='float' ,def_val=1.23            ,comment= 'smth')
#                   ,dict(key='key-aflo'                ,def_val=1.23            ,comment= 'smth')
#                   ,dict(key='key-font',format='font'  ,def_val=''              ,comment= 'smth')
#                   ,dict(key='key-file',format='file'  ,def_val=''              ,comment= 'smth')
#                   ,dict(key='key-en_i',format='enum_i',def_val=1               ,comment= 'smth',   dct={0:'000', 1:'111', 2:'222'})
#                   ,dict(key='key-en_s',format='enum_s',def_val='b'             ,comment= 'smth',   dct=[('a','AA'), ('b','BB'), ('c','CC')])
#                   ,dict(key='key-json',format='json'  ,def_val={'x':{'a':1}}   ,comment= 'Style')
#                   ]
#       path_to_json=os.path.dirname(__file__)+os.sep+'test.json'

    if 0==len(keys_info):
        return app.msg_status(_('Empty keys_info'))

    # Start COMMON STATIC data
    fltr_h  = _('Suitable keys will contain all specified words.'
              '\rTips:'
              '\r • Start with "*" to view only changed values.'
              '\r • Use "<" or ">" for word boundary.'
              '\r     size> <tab'
              '\r   selects "tab_size" but not "ui_tab_size" or "tab_size_x".'
              '\rAlt+L - Clear filter')
    chap_h  = _('Only in selected chapter.'
              '\rAlt+E - In all Chapters')
    t1st_c  = _('Conf&igured first')
    t1st_h  = _('Show user keys on top of entire list.'
              '\rThe order of keys will be the same as in user file.')
    trgt_h  = _('Set storage for values')
    rprt_h  = _('Create HTML report and open it in browser')

    font_l  = [] if app.app_api_version()<'1.0.174' else \
              [font 
                for font in app.app_proc(app.PROC_ENUM_FONTS, '')
                if not font.startswith('@')] 
    font_l  = ['default'] + font_l
    # Finish COMMON STATIC data

    # Start COMMON DINAMIC data
    stores  = json.loads(open(CFG_JSON).read(), object_pairs_hook=odict) \
                if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
              odict()

    chap_l  = list({kinfo.get('chapter', '') for  kinfo in keys_info if kinfo.get('chapter', '')})
    chap_l  = [' '] + sorted(chap_l)
    chap_vl = [len(['' for kinfo in keys_info if chp==kinfo.get('chapter', '')]) for chp in chap_l if chp!=' ']
    chap_vl = [''] + [f(' ({})', str(chp)) for chp in chap_vl]
    tag_set = set()
    for  kinfo in keys_info:
        tag_set.update({t for t in kinfo.get('tags', [])})
    tags_l  = sorted(list(tag_set))
    tags_vl = [len(['' for kinfo in keys_info if tag in kinfo.get('tags', [])]) for tag in tags_l]
    tags_vl = [f(' ({})', str(tag)) for tag in tags_vl]
    pass;                      #LOG and log('chap_l={}',(chap_l))
    pass;                      #LOG and log('chap_vl={}',(chap_vl))
    pass;                      #LOG and log('tags_l={}',(tags_l))
    pass;                      #LOG and log('tags_vl={}',(tags_vl))

    t1st_b  = stores.get('t1st', False)
    k2fdcvt = get_main_data(keys_info, trgt_1st=t1st_b)
    pass;                      #LOG and log('k2fdcvt={}',(k2fdcvt))

    trgt_s  = 'user.json'
    key_sel = keys_info[0]['key']
    cond_s  = ''
    chap_s  = stores.get(subset+'chap')
    chap_n  = index_1(chap_l, chap_s, 0)
    tags_set= {tag for tag in stores.get(subset+'tags', []) if tag in tags_l}
    tags_s  = '#'+', #'.join(tags_set)  if tags_set else ''
    stores[subset+'h.tags']= add_to_history(tags_s, stores.get(subset+'h.tags', []), MAX_HIST, unicase=False)
    tags_hl = [s for s in stores.get(subset+'h.tags', []) if s ]
    tags_n  = 0 if tags_s and tags_hl else -1
    fid     = 'lvls'
    # Finish COMMON DINAMIC data
    while True: #NOTE: json_props
        COL_WS      = [                 stores.get(subset+'cust.wd_k', 250)
#                     ,                 stores.get(subset+'cust.wd_f',  50)
                      ,                 stores.get(subset+'cust.wd_s',  20)
                      ,                 stores.get(subset+'cust.wd_v', 250)]         # Widths of listview columns 
        CMNT_H      =                   stores.get(subset+'cust.ht_c', 100)          # Height of Comment memo
        LST_W, LST_H= sum(COL_WS)+20,   stores.get(subset+'cust.ht_t', 300)-5        # Listview sizes
        DLG_W, DLG_H= 5+LST_W+5+80+5 \
                    , 5+20+30+LST_H+5+30+5+30+5+CMNT_H+5     # Dialog sizes
        l_val   = DLG_W-10-80-20-COL_WS[-1]
        
        # Filter with 
        #   cond_s
        #   chap_n, chap_s
        #   tags_set
        chap_s  = chap_l[chap_n]
        pass;                  #LOG and log('chap_n,chap_s={}',(chap_n,chap_s))
        only_chd= cond_s.startswith('*')
        cond_4f = (cond_s if not only_chd else cond_s[1:]).upper()
        fl_kfsvt= [ (knm
                    ,fdcv['f']
                    ,'*' if fdcv['d']!=fdcv['v'] else ''
#                   ,fdcv['v']
                    ,fdcv['v'] if type(fdcv['v'])!=bool else str(fdcv['v']).lower()
                    ,fdcv['t']
                    ,f('{}: ',fdcv['a'])                if chap_l and chap_n==0 and fdcv['a'] else ''
                    ,f(' (#{})',', #'.join(fdcv['g']))  if tags_l and               fdcv['g'] else ''
                    )
                    for (knm, fdcv) in k2fdcvt.items()
                    if  (not only_chd   or fdcv['d']!=fdcv['v'])            and
                        (cond_4f==''    or test_cond(cond_4f, knm))  and
                        (chap_n==0      or chap_s==fdcv['a'])               and
                        (not tags_set   or (tags_set & fdcv['g']))
                 ]
        fl_k2i  = {knm:ikey for (ikey, (knm,kf,kset,kv,kdct,kch,ktg)) in enumerate(fl_kfsvt)}
        ind_sel = fl_k2i[key_sel]       if key_sel in fl_k2i                else \
                  0                     if fl_k2i                           else \
                  -1
        key_sel = fl_kfsvt[ind_sel][0]  if ind_sel!=-1                      else ''
        frm_sel = k2fdcvt[key_sel]['f'] if key_sel                          else ''
        dct_sel = k2fdcvt[key_sel]['t'] if key_sel                          else None
        dvl_sel = k2fdcvt[key_sel]['d'] if key_sel                          else None
        val_sel = k2fdcvt[key_sel]['v'] if key_sel                          else None
        cmt_sel = k2fdcvt[key_sel]['c'] if key_sel                          else ''
        var_sel = [f('{}: {}', k, v) for (k,v) in dct_sel.items()] \
                                        if frm_sel in ('enum_i', 'enum_s')  else \
                  font_l + ([] if val_sel in font_l else [val_sel])              \
                                        if frm_sel=='font' and     font_l   else \
                  []
        sel_sel = index_1(list(dct_sel.keys()), val_sel) \
                                        if frm_sel in ('enum_i', 'enum_s')  else \
                  index_1(font_l,               val_sel, len(font_l))            \
                                        if frm_sel=='font' and     font_l   else \
                  -1
        pass;                  #LOG and log('sel_sel,var_sel={}',(sel_sel,var_sel))

        stat    = f(' ({}/{})', len(fl_kfsvt), len(k2fdcvt))
        col_aws = [p+cw for (p,cw) in zip(('',      'C', ''), map(str, COL_WS))]
        itms    = (zip([_('Key')+stat,              _(' '), f(_('Value from "{}"'), trgt_s)], col_aws)
                  ,    [ ( kch+knm+ktg,                kset,   to_str(kv, kf, kdct)) for
                         (     knm,       kf,          kset,          kv,     kdct, kch, ktg ) in fl_kfsvt]
                  )
        pass;                  #LOG and log('cond_s={}',(cond_s))
        pass;                  #LOG and log('fl_kfsvt={}',(fl_kfsvt))
        pass;                  #LOG and log('fl_k2i={}',(fl_k2i))
        pass;                  #LOG and log('key_sel,ind_sel={}',(key_sel, ind_sel))
        cond_hl = [s for s in stores.get(subset+'h.cond', []) if s ]
        
        chap_v  = [chp+chp_vl for (chp,chp_vl) in zip(chap_l, chap_vl)]
        tags_hl = [s for s in stores.get(subset+'h.tags', []) if s ]
        
        as_bool = key_sel and  frm_sel in ('bool')
        as_char = key_sel and (frm_sel in ('int', 'float', 'str', 'json')   or frm_sel=='font' and not bool(font_l))
        as_enum = key_sel and (frm_sel in ('enum_i', 'enum_s')              or frm_sel=='font' and     bool(font_l))
        as_file = key_sel and  frm_sel in ('file')
        as_hotk = key_sel and  frm_sel in ('hotk')
        font_nm4sz  = key_sel.replace('font_size', 'font_name')
        font_sz4nm  = key_sel.replace('font_name', 'font_size')
        pvw_font_ns = None \
                    if not font_l                                                              else \
                  (val_sel,                 k2fdcvt[font_sz4nm]['v'])                               \
                    if frm_sel=='font' and val_sel!='default'       and font_sz4nm in k2fdcvt  else \
                  (k2fdcvt[font_nm4sz]['v'], val_sel                )                               \
                    if frm_sel=='int' and 'font_size' in key_sel    and font_nm4sz in k2fdcvt  else \
                  None
        pass;                  #LOG and log('pvw_font_ns={}',(pvw_font_ns))
        w_chap  = len(chap_l)>1
        w_tags  = bool(tags_l)
        pass;                  #LOG and log('(w_chap,w_tags),(as_bool,as_char,as_enum,as_file)={}',((w_chap,w_tags),(as_bool,as_char,as_enum,as_file)))
        cnts    =[                                                                                                                                              # bdgkmopqswxyz
    # Chapters
      dict(            tp='lb'  ,t=5        ,l=15+COL_WS[0] ,w=140          ,cap=_('Se&ction:') ,hint=chap_h            ,vis=w_chap             )   # &c
     ,dict( cid='chap',tp='cb-r',t=25       ,l=15+COL_WS[0] ,w=140          ,items=chap_v                       ,act='1',vis=w_chap             )   #
     ,dict( cid='-cha',tp='bt'  ,t=0        ,l=0            ,w=0            ,cap='&e'                                   ,vis=w_chap             )   # &e
    # Tags
     ,dict(            tp='lb'  ,t=5        ,l=COL_WS[0]+160,r=DLG_W-10-80  ,cap=_('T&ags:')                            ,vis=w_tags             )   # &a
     ,dict( cid='tags',tp='cb-r',t=25       ,l=COL_WS[0]+160,r=DLG_W-10-80  ,items=tags_hl                      ,act='1',vis=w_tags             )   #
     ,dict( cid='?tgs',tp='bt'  ,tid='tags' ,l=DLG_W-5-80   ,w=80           ,cap=_('Tag&s…')    ,hint=_('Choose tags')  ,vis=w_tags             )   # &s
     ,dict( cid='-tgs',tp='bt'  ,t=57       ,l=DLG_W-5-80   ,w=80           ,cap=_('Clea&r')    ,hint=_('Clear tags')   ,vis=w_tags             )   # &r
    # Filter
     ,dict( cid='-flt',tp='bt'  ,t=0        ,l=0            ,w=0            ,cap='&l'                                                           )   # &l
     ,dict( cid='fltr',tp='bt'  ,t=0        ,l=0            ,w=0            ,cap=''                 ,def_bt='1'                                 )   # 
     ,dict(            tp='lb'  ,t=5        ,l=5+2          ,w=COL_WS[0]    ,cap=_('&Filter:')  ,hint=fltr_h                                    )   # &f
     ,dict( cid='cond',tp='cb'  ,t=25       ,l=5+2          ,w=COL_WS[0]    ,items=cond_hl                                                      )   #
    # Table of keys+values
     ,dict( cid='lvls',tp='lvw' ,t=57       ,l=5 ,h=LST_H   ,w=LST_W        ,items=itms             ,grid='1'   ,act='1'                        )   #
    # Editors for value
     ,dict(            tp='lb'  ,tid='t1st' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                                                  )   # &v 
     ,dict( cid='edch',tp='ch'  ,tid='t1st' ,l=l_val+5      ,w=COL_WS[-1]+15,cap=_('O&n')                       ,act='1',vis=as_bool            )   # &n
     ,dict( cid='eded',tp='ed'  ,tid='t1st' ,l=l_val+5      ,w=COL_WS[-1]+15-(30 if as_file or as_hotk else 0)          ,vis=as_char or as_file or as_hotk 
                                                                                                ,en=as_char or as_file)   #
     ,dict( cid='brow',tp='bt'  ,tid='t1st' ,l=DLG_W-5-80-35,w=30           ,cap=_('&...') ,hint=_('Choose')            ,vis=as_file or as_hotk )   # &.
     ,dict( cid='setv',tp='bt'  ,tid='t1st' ,l=DLG_W-5-80   ,w=80           ,cap=_('Cha&nge')   ,en=(frm_sel!='json')   ,vis=as_char or as_file )   # &n
     ,dict( cid='edcb',tp='cb-r',tid='t1st' ,l=l_val+5      ,w=COL_WS[-1]+15,items=var_sel                      ,act='1',vis=as_enum            )   #
    # View def-value
     ,dict(            tp='lb'  ,tid='dfvl' ,l=l_val-100-5  ,w=100          ,cap=_('>Default value:')                                           )   # 
     ,dict( cid='dfvl',tp='ed'  ,t=93+LST_H ,l=l_val+5      ,w=COL_WS[-1]+15                        ,ro_mono_brd='1,0,1'                        )   #
     ,dict( cid='setd',tp='bt'  ,tid='dfvl' ,l=DLG_W-5-80   ,w=80           ,cap=_('Reset')     ,en=(dvl_sel!=val_sel and  frm_sel!='json')     )   # 
    # Comment
     ,dict( cid='cmnt',tp='memo',t=125+LST_H,l=5 ,h=CMNT_H-3,w=LST_W                                ,ro_mono_brd='1,1,1'                        )   #
    # Target json
     ,dict( cid='trgt',tp='bt'  ,t=120      ,l=DLG_W-5-80   ,w=80           ,cap=_('&Target…')  ,hint=trgt_h                                    )   # &t
     ,dict( cid='cust',tp='bt'  ,t=150      ,l=DLG_W-5-80   ,w=80           ,cap=_('Ad&just…')                                                  )   # &j
     ,dict( cid='rprt',tp='bt'  ,t=DLG_H-65 ,l=DLG_W-5-80   ,w=80           ,cap=_('Report…')   ,hint=rprt_h                                    )   # &h
     ,dict( cid='-'   ,tp='bt'  ,t=DLG_H-35 ,l=DLG_W-5-80   ,w=80           ,cap=_('Close')                                                     )   #
     ,dict( cid='t1st',tp='ch'  ,t=65+LST_H ,l=5            ,w=100          ,cap=t1st_c         ,hint=t1st_h    ,act='1'                        )   # &i
                 ]
        if pvw_font_ns: # View commnent with tested font
            [cnt for cnt in cnts if cnt.get('cid')=='cmnt'][0].update(
                dict(font_name=pvw_font_ns[0], font_size=pvw_font_ns[1] ,ro_mono_brd='1,0,1'))
        vals    =       dict(cond=cond_s
                            ,lvls=ind_sel
                            ,t1st=t1st_b
                            ,dfvl=to_str(dvl_sel, frm_sel, dct_sel)     if key_sel else ''
                            ,cmnt=cmt_sel.replace('\r', '\n')           if key_sel else ''
                            )
        if 1<len(chap_l):
            vals.update(dict(chap=chap_n))
        if tags_l:
            vals.update(dict(tags=tags_n))
        if as_bool:
            vals.update(dict(edch=val_sel                               if key_sel else False))
        if as_char or as_file or as_hotk:
            vals.update(dict(eded=to_str(val_sel, frm_sel, dct_sel)     if key_sel else ''  ))
        if as_enum:
            vals.update(dict(edcb=sel_sel                               if key_sel else False))

       #pass;                   LOG and log('cnts={}',(cnts))
        aid, vals, fid, chds = dlg_wrapper(f('{} ({})', title, VERSION_V), DLG_W, DLG_H, cnts, vals, focus_cid=fid)
        if aid is None or aid=='-':  return

        if aid=='-flt':
            vals['cond']    = ''
        if aid=='-cha':
            vals['chap']    = 0
        if aid=='fltr' and fid=='eded':     # Подмена умолчательной кнопки по активному редактору
            aid = 'setv'

        pass;                  #    LOG and log('aid={}',(aid))

        fid     = 'lvls'
        cond_s  = vals['cond']
        chap_n  = vals['chap']  if 1<len(chap_l)    else chap_n
        ind_sel = vals['lvls']
        t1st_b  = vals['t1st']

        stores[subset+'h.cond'] = add_to_history(cond_s, stores.get(subset+'h.cond', []), MAX_HIST, unicase=False)
        stores[subset+'chap']   = chap_l[chap_n]
        stores['t1st']          = t1st_b
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))

        if aid=='cust':
            custs   = app.dlg_input_ex(5, _('Adjust')
                  , _(  'Height of Table (min 125)')  , str(stores.get(subset+'cust.ht_t', 300))
                  , _(     'Width of Key (min 250)')  , str(stores.get(subset+'cust.wd_k', 250))
                  , _(       'Width of * (min  20)')  , str(stores.get(subset+'cust.wd_s',  20))
                  , _(   'Width of Value (min 250)')  , str(stores.get(subset+'cust.wd_v', 250))
                  , _('Height of Comment (min  55)')  , str(stores.get(subset+'cust.ht_c', 100))
                    )
            if custs is None:   continue#while
            stores[subset+'cust.ht_t']  = max(125, int(custs[0]))
            stores[subset+'cust.wd_k']  = max(250, int(custs[1]))
            stores[subset+'cust.wd_s']  = max( 20, int(custs[2]))
            stores[subset+'cust.wd_v']  = max(250, int(custs[3]))
            stores[subset+'cust.ht_c']  = max( 55, int(custs[4]))
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            continue#while
            
        if aid=='t1st':     # Show user key first
            k2fdcvt = get_main_data(keys_info, trgt_s, t1st_b)
        if aid=='tags':     # Use prev tag set
            ind     = vals['tags']
            tags_s  = tags_hl[ind]
            tags_set= set(tags_s.replace('#', '').replace(' ', '').split(','))
            tags_n  = 0
            stores[subset+'h.tags']= add_to_history(tags_s, stores.get(subset+'h.tags', []), MAX_HIST, unicase=False)
            stores[subset+'tags']  = list(tags_set)
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        if aid=='-tgs':     # Clear tags
            tags_s  = ''
            tags_set= set()
            tags_n  = -1
            stores[subset+'h.tags']= add_to_history(tags_s, stores.get(subset+'h.tags', []), MAX_HIST, unicase=False)
            stores[subset+'tags']  = list(tags_set)
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        if aid=='?tgs':     # Choose any tags
            sels    = ['1' if tag in tags_set else '0' for tag in tags_l]
            crt     = str(sels.index('1') if '1' in sels else 0)
            tags_v  = [tag+tag_v for (tag,tag_v) in zip(tags_l, tags_vl)]
            tg_aid, \
            tg_vals,\
            *_t     = dlg_wrapper(f(_('Tags ({})'), len(tags_l)), GAP+200+GAP, GAP+400+GAP+24+GAP, 
                    [ dict(cid='tgs',tp='ch-lbx',t=5,h=400  ,l=5            ,w=200  ,items=tags_v           ) #
                     ,dict(cid='!'  ,tp='bt'    ,t=5+400+5  ,l=    200-140  ,w=70   ,cap=_('OK'),props='1'  ) #  default
                     ,dict(cid='-'  ,tp='bt'    ,t=5+400+5  ,l=5  +200- 70  ,w=70   ,cap=_('Cancel')        ) #  
                    ]
                    , dict(tgs=(crt,sels)), focus_cid='tgs')
            if tg_aid=='!':
                crt,sels= tg_vals['tgs']
                tags    = [tag for (ind,tag) in enumerate(tags_l) if sels[ind]=='1']
                tags_set= set(tags)
                tags_s  = '#'+', #'.join(tags)  if tags else ''
                tags_n  = 0                     if tags else -1
                stores[subset+'h.tags']= add_to_history(tags_s, stores.get(subset+'h.tags', []), MAX_HIST, unicase=False)
                stores[subset+'tags']  = list(tags_set)
                open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        
        if ind_sel==-1:  continue#while
        key_sel = fl_kfsvt[ind_sel][0]
        pass;                  #LOG and log('cond_s={}',(cond_s))

        if aid=='setd' and dvl_sel!=val_sel:
            # Reset def value
            k2fdcvt[key_sel]['v'] = dvl_sel
            # Update json file
            apx.set_opt(key_sel, dvl_sel)
            ed.cmd(cmds.cmd_OpsReloadAndApply)
            dvl_sel_s = repr(dvl_sel) if type(dvl_sel)!=bool else str(dvl_sel).lower()
            app.msg_status( f(_('Change in {}: "{}": {} (default value)'), trgt_s, key_sel, dvl_sel_s))
            print(          f(_('Change in {}: "{}": {} (default value)'), trgt_s, key_sel, dvl_sel_s))
        if aid in ('edch', 'eded', 'edcb', 'setv', 'brow'): #NOTE: if aid in ('edch', 'eded', 'edcb', 'setv', 'brow'):
            # Changed value
            old_val = k2fdcvt[key_sel]['v']
            
            if as_bool and aid=='edch':
                k2fdcvt[key_sel]['v'] = not k2fdcvt[key_sel]['v']
            if aid=='setv':
                new_val = vals['eded']
                good    = False
                while not good:
                    try:
                        k2fdcvt[key_sel]['v'] = from_str(new_val, k2fdcvt[key_sel]['f'])
                        good    = True
                    except Exception as ex:
                        good    = False
                        app.msg_status(_('Uncorrect value'))
                    if not good:
                        new_val = app.dlg_input(f(_('Value of "{}" (type "{}")'), key_sel, k2fdcvt[key_sel]['f']), new_val)
                        if new_val is None:
                            break#while not good
                    #while not good
            if as_enum and aid=='edcb' and vals['edcb']!=-1:
                ind     = vals['edcb']
                val_l   = font_l    if frm_sel=='font' else     list(dct_sel.keys())
#               val_l   = font_l    if frm_sel=='font' else     list(var_sel.keys())
                k2fdcvt[key_sel]['v'] = val_l[ind]
            if aid=='brow' and as_file:
                path    = app.dlg_file(True, '', os.path.expanduser(k2fdcvt[key_sel]['v']), '')
                if not path:  continue#while
                k2fdcvt[key_sel]['v'] = path
            if aid=='brow' and as_hotk:
                hotk    = app.dlg_hotkey(f('{}: {}', key_sel, k2fdcvt[key_sel]['v']))
                if not hotk:  continue#while
                k2fdcvt[key_sel]['v'] = hotk

            new_val = k2fdcvt[key_sel]['v']
            if old_val != new_val:
                # Update json file
                if trgt_s=='user.json':
                    apx.set_opt(key_sel, new_val)
                else:
                    opts_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+trgt_s
                    opts        = apx._get_file_opts(opts_json)
                    if new_val==opts.get(key_sel, dvl_sel): continue#while
                    if new_val==dvl_sel:
                        opts.pop(key_sel, None)
                    else:
                        opts[key_sel]   = new_val
                    open(opts_json,'w').write(json.dumps(opts, indent=2))
                ed.cmd(cmds.cmd_OpsReloadAndApply)
                new_val_s = repr(new_val) if type(new_val)!=bool else str(new_val).lower()
                app.msg_status( f(_('Change in {}: "{}": {}'), trgt_s, key_sel, new_val_s))
                print(          f(_('Change in {}: "{}": {}'), trgt_s, key_sel, new_val_s))
            
        if aid=='rprt':
            htm_file = os.path.join(tempfile.gettempdir(), 'CudaText_option_report.html')
            if not do_report(htm_file, '' if trgt_s=='user.json' else trgt_s): continue#while
            webbrowser.open_new_tab('file://'+htm_file)
            app.msg_status('Opened browser with file '+htm_file)

        if aid=='trgt':
            trgt_l  = []
            trgt_n  = None
            for all_b in (False, True):
#               trgt_l  = ['lexer '+lxr+'.json' 
#                           for lxr in app.lexer_proc(app.LEXER_GET_LIST, '').splitlines() 
#                           if app.lexer_proc(app.LEXER_GET_ENABLED, lxr) and 
#                           (all_b or os.path.isfile(app.app_path(app.APP_DIR_SETTINGS)+os.sep+'lexer '+lxr+'.json'))
#                         ]
                trgt_l  = ['lexer '+lxr+'.json' 
                            for lxr in app.lexer_proc(app.LEXER_GET_LEXERS, False) #only shown lexers
                            if (all_b or os.path.isfile(app.app_path(app.APP_DIR_SETTINGS)+os.sep+'lexer '+lxr+'.json'))
                          ]
                trgt_l  = ['user.json'] + trgt_l
                trgt_n  = app.dlg_menu(app.MENU_LIST
                                      ,'\n'.join(trgt_l+([] if all_b else [_('[Show all lexers]')]))
                                      ,index_1(trgt_l, trgt_s, 0)
                                      )
                if trgt_n is None:          break#for
                pass;          #LOG and log('trgt_n={}',(trgt_n))
                if trgt_n == len(trgt_l):   continue#for with all_b=True
                break#for
               #for all_b
            if trgt_n is None:              continue#while
            new_trgt_s  = trgt_l[trgt_n]
            pass;              #LOG and log('new_trgt_s={}',(new_trgt_s))
            if new_trgt_s!=trgt_s:
                k2fdcvt = get_main_data(keys_info, new_trgt_s, t1st_b)
                trgt_s  = new_trgt_s
       #while
   #def dlg_opt_editor_wr

def add_to_history(val:str, lst:list, max_len:int, unicase=True)->list:
    """ Add/Move val to list head. """
    lst_u = [ s.upper() for s in lst] if unicase else lst
    val_u = val.upper()               if unicase else val
    if val_u in lst_u:
        if 0 == lst_u.index(val_u):   return lst
        del lst[lst_u.index(val_u)]
    lst.insert(0, val)
    if len(lst)>max_len:
        del lst[max_len:]
    return lst
   #def add_to_history
    
def frm_of_val(val):
    if isinstance(val, bool):   return 'bool'
    if isinstance(val, int):    return 'int'
    if isinstance(val, float):  return 'float'
    if isinstance(val, str):    return 'str'
    pass;                       return ''
   #def frm_of_val
    
def to_str(kv, kformat, dct=None):
    'Convert a value of key to string to show (in listview cell, in edit)'
    if kformat=='json' \
    or isinstance(kv, dict) or isinstance(kv, list):
        return json.dumps(kv)
    if kformat=='enum_i' and dct is not None:
        return dct.get(kv, str(kv))
    if kformat=='enum_s' and dct is not None:
        return dct.get(str(kv), str(kv))
    return str(kv)
   #def to_str
    
def from_str(strv, kformat, dct=None):
    'Convert a value of key to string to show (in listview cell, in edit)'
    if kformat in ('bool'):
        return bool(strv)
    if kformat in ('int'):
        return int(strv)
    if kformat in ('float'):
        return float(strv)
    if kformat in ('str'):
        return strv
    if kformat=='json' \
    or isinstance(strv, dict) or isinstance(strv, list):
        return json.loads(strv, object_pairs_hook=odict)
    if kformat in ('enum_i', 'enum_s') and dct is not None:
        ind = list(dct.values()).index(strv)
        ans = list(dct.keys())[ind]
        return int(ans) if kformat=='enum_i' else ans 
    return strv
   #def from_str
    
reNotWdChar = re.compile(r'\W')
def test_cond(cnd_s, text):
    if not cnd_s:       return True
    text    = text.upper()
    if '<' in cnd_s or '>' in cnd_s:
        text    = '·' + reNotWdChar.sub('·', text)    + '·'
        cnd_s   = ' ' + cnd_s + ' '
        cnd_s   = cnd_s.replace(' <', ' ·').replace('> ', '· ')
    pass;                  #LOG and log('cnd_s, text={}',(cnd_s, text))
    return all(map(lambda c:c in text, cnd_s.split()))
   #def test_cond

def get_main_data(keys_info, trgt_json='user.json', trgt_1st=False):
    opts_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+trgt_json
    trgt_opts   = apx._json_loads(open(opts_json, encoding='utf8').read(), object_pairs_hook=odict) \
                    if os.path.isfile(opts_json) else {}
#   trgt_opts   = apx._get_file_opts(opts_json, object_pairs_hook=odict)
#   nonlocal keys_info
    keys_info_  = keys_info.copy()
    if trgt_1st:
        keys_d      = odict([(ki['key'],ki) for ki in keys_info])
        keys_info_  = [keys_d[k] for k  in trgt_opts if k             in keys_d] \
                    + [ki        for ki in keys_info if ki['key'] not in trgt_opts]
    return odict([
        (       kinfo['key'],
           {'f':kinfo.get('format', frm_of_val(kinfo['def_val']))
           ,'t':kinfo.get('dct')            if ('dct' not in kinfo or   isinstance(kinfo.get('dct'), dict)) else 
                odict(kinfo.get('dct'))
           ,'d':kinfo['def_val']
           ,'c':kinfo['comment']            if                          isinstance(kinfo['comment'], str) else
                '\n'.join(kinfo['comment'])
           ,'v':trgt_opts.get(kinfo['key'], kinfo['def_val'])
           ,'a':kinfo.get('chapter', '')
           ,'g':set(kinfo.get('tags', []))
           }
        )  for  kinfo in keys_info_
        ])
   #def get_main_data


def parse_raw_keys_info(path_to_raw):
    pass;                      #LOG and log('path_to_raw={}',(path_to_raw))
    #NOTE: parse_raw
    kinfs    = []
    lines   = open(path_to_raw, encoding='utf8').readlines()
#   if 'debug'=='debug':        lines = ['  //[FindHotkeys]'
#                                       ,'  //Hotkeys in Find/Replace dialog'
#                                       ,'  "find_hotkey_find_first": "Alt+Enter",'
#                                       ,'  "find_hotkey_replace": "Alt+Z",'
#                                       ,'  "find_hotkey_find_dlg": "Ctrl+F",'
#                                       ,'  '
#                                       ,'  //UI elements font name [has suffix]'
#                                       ,'  "ui_font_name": "default",'
#                                       ]

    l       = '\n'
    
    reTags  = re.compile(r' *\((#\w+,?)+\)')
#   reN2S   = re.compile(r'\s+(\d+): *(.+)')
#   reS2S   = re.compile(r'\s+"(\w*)": *(.+)')
    reN2S   = re.compile(r'^\s*(\d+): *(.+)'    , re.M)
    reS2S   = re.compile(r'^\s*"(\w*)": *(.+)'  , re.M)
    reLike  = re.compile(r' *\(like (\w+)\)')
    reFldFr = re.compile(r'\s*Folders from: (.+)')
    def parse_cmnt(cmnt, frm, kinfs):  
        tags= set()
        mt  = reTags.search(cmnt)
        while mt:
            tags_s  = mt.group(0)
            tags   |= set(tags_s.strip(' ()').replace('#', '').split(','))
            cmnt    = cmnt.replace(tags_s, '')
            mt      = reTags.search(cmnt)
        dctN= [[int(m.group(1)), m.group(2).rstrip(', ')] for m in reN2S.finditer(cmnt+l)]
        dctS= [[    m.group(1) , m.group(2).rstrip(', ')] for m in reS2S.finditer(cmnt+l)]
        frmK,\
        dctK= frm, None
        mt  = reLike.search(cmnt)
        if mt:
            ref_knm = mt.group(1)
            ref_kinf= [kinf for kinf in kinfs if kinf['key']==ref_knm]
            if not ref_kinf:
                log('Error on parse {}. No ref-key {} from comment\n{}',(path_to_raw, ref_knm, cmnt))
            else:
                ref_kinf = ref_kinf[0]
                frmK= ref_kinf['format']    if 'format' in ref_kinf else    frmK
                dctK= ref_kinf['dct']       if 'dct'    in ref_kinf else    dctK
        dctF= None
        mt  = reFldFr.search(cmnt)
        if mt:
            from_short  = mt.group(1)
            from_dir    = from_short if os.path.isabs(from_short) else os.path.join(app.app_path(app.APP_DIR_DATA), from_short)
            pass;              #LOG and log('from_dir={}',(from_dir))
            if not os.path.isdir(from_dir):
                log(_('No folder "{}" from\n{}'), from_short, cmnt)
            else:
                dctF    = {d:d for d in os.listdir(from_dir) if os.path.isdir(from_dir+os.sep+d)}
        frm,\
        dct = ('enum_i', dctN)    if dctN else \
              ('enum_s', dctS)    if dctS else \
              (frmK,     dctK)    if dctK else \
              ('enum_s', dctF)    if dctF else \
              (frm     , []  )
        return cmnt, frm, dct, list(tags)
       #def parse_cmnt
    def jsstr(s):
        return s[1:-1].replace(r'\"','"').replace(r'\\','\\')
    
    reChap1 = re.compile(r' *//\[Section: +(.+)\]')
    reChap2 = re.compile(r' *//\[(.+)\]')
    reCmnt  = re.compile(r' *//(.+)')
    reKeyDV = re.compile(r' *"(\w+)" *: *(.+)')
    reInt   = re.compile(r' *(-?\d+)')
    reFloat = re.compile(r' *(-?\d+\.\d+)')
    reFontNm= re.compile(r'font\w*_name')
    reHotkey= re.compile(r'_hotkey_')
    chap    = ''
    ref_cmnt= ''    # Full comment to add to '... smth'
    pre_cmnt= ''
    cmnt    = ''
    for line in lines:
        if False:pass
        elif    reChap1.match(line):
            mt= reChap1.match(line)
            chap    = mt.group(1)
            cmnt    = ''
        elif    reChap2.match(line):
            mt= reChap2.match(line)
            chap    = mt.group(1)
            cmnt    = ''
        elif    reCmnt.match(line):
            mt= reCmnt.match(line)
            cmnt   += l+mt.group(1)
        elif    reKeyDV.match(line):
            mt= reKeyDV.match(line)
            key     = mt.group(1)
            dval_s  = mt.group(2).rstrip(', ')
            cmnt    = cmnt.strip(l)     if cmnt else pre_cmnt
            frm,dval= \
                      ('bool', True         )   if dval_s=='true'                       else \
                      ('bool', False        )   if dval_s=='false'                      else \
                      ('float',float(dval_s))   if reFloat.match(dval_s)                else \
                      ('int',  int(  dval_s))   if reInt.match(dval_s)                  else \
                      ('font', dval_s[1:-1] )   if reFontNm.search(key)                 else \
                      ('hotk', dval_s[1:-1] )   if reHotkey.search(key)                 else \
                      ('str',  jsstr(dval_s))   if dval_s[0]=='"' and dval_s[-1]=='"'   else \
                      ('unk',  dval_s       )
            pass;              #LOG and log('key,dval_s,frm,dval={}',(key,dval_s,frm,dval))
            
            ref_cmnt= ref_cmnt                                      if cmnt.startswith('...') else cmnt
            kinf    = odict()
            kinfs  += [kinf]
            kinf['key']             = key
            kinf['def_val']         = dval
            kinf['comment']         = cmnt
            kinf['format']          = frm
            if frm in ('int','str'):
                cmnt,frm,dct,tags   = parse_cmnt(ref_cmnt+l+cmnt[3:]    if cmnt.startswith('...') else cmnt, frm, kinfs)
                kinf['comment']     = cmnt
                if frm in ('enum_i','enum_s'):
                    kinf['format']  = frm
                if dct:
                    log('Too few variants ({}) for key {}',len(dct), key) if len(dct)<2 else None
                    kinf['dct']     = dct
                if tags:
                    kinf['tags']    = tags
            if chap:
                kinf['chapter']     = chap
            pre_cmnt= cmnt              if cmnt else pre_cmnt
            cmnt    = ''
       #for line
    return kinfs
   #def parse_raw_keys_info

RPT_HEAD = '''
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>CudaText options</title>
    <style type="text/css">
td, th, body {
    color:          #000;
    font-family:    Verdana, Arial, Helvetica, sans-serif;
    font-size:      12px;
}
table {
    border-width:   1px;
    border-spacing: 2px;
    border-color:   gray;
    border-collapse:collapse;
}
table td, table th{
    border-width:   1px;
    padding:        1px;
    border-style:   solid;
    border-color:   gray;
}
pre {
    margin:         0;
    padding:        0;
}
td.nxt {
    color:          grey;
}
td.win {
    font-weight:    bold;
}
    </style>
</head>
<body>
'''
RPT_FOOT = '''
</body>
</html>
'''

def do_report(fn, lex=''):
#   lex         = ed.get_prop(app.PROP_LEXER_CARET)
    def_json    = apx.get_def_setting_dir()         +os.sep+'default.json'
    usr_json    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'user.json'
    lex_json    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+lex                                 if lex else ''

    def_opts    = apx._get_file_opts(def_json, {},  object_pairs_hook=collections.OrderedDict)
    usr_opts    = apx._get_file_opts(usr_json, {},  object_pairs_hook=collections.OrderedDict)
    lex_opts    = apx._get_file_opts(lex_json, {},  object_pairs_hook=collections.OrderedDict)  if lex else None

    def_opts    = pickle.loads(pickle.dumps(def_opts))                              # clone to pop
    usr_opts    = pickle.loads(pickle.dumps(usr_opts))                              # clone to pop
    lex_opts    = pickle.loads(pickle.dumps(lex_opts))  if lex else {}              # clone to pop

    fil_opts    = get_ovrd_ed_opts(ed)
    cmt_opts    = {}
    # Find Commentary for def opts in def file
    # Rely: _commentary_ is some (0+) lines between opt-line and prev opt-line
    def_body    = open(def_json).read()
    def_body    = def_body.replace('\r\n', '\n').replace('\r', '\n')
    def_body    = def_body[def_body.find('{')+1:]   # Cut head with start '{'
    def_body    = def_body.lstrip()
    for opt in def_opts.keys():
        pos_opt = def_body.find('"{}"'.format(opt))
        cmt     = def_body[:pos_opt].strip()
        cmt     = ('\n\n'+cmt).split('\n\n')[-1]
        cmt     = re.sub('^\s*//', '', cmt, flags=re.M)
        cmt     = cmt.strip()
        cmt_opts[opt]    = html.escape(cmt)
        def_body= def_body[def_body.find('\n', pos_opt)+1:]   # Cut the opt

    with open(fn, 'w', encoding='utf8') as f:
        f.write(RPT_HEAD)
        f.write('<h4>High priority: editor options</h4>')
        f.write('<table>\n')
        f.write(    '<tr>\n')
        f.write(    '<th>Option name</th>\n')
        f.write(    '<th>Value in<br>default</th>\n')
        f.write(    '<th>Value in<br>user</th>\n')
        f.write(    '<th>Value in<br>{}</th>\n'.format(lex))                                                            if lex else None
        f.write(    '<th title="{}">Value for file<br>{}</th>\n'.format(ed.get_filename()
                                              , os.path.basename(ed.get_filename())))
        f.write(    '<th>Comment</th>\n')
        f.write(    '</tr>\n')
        for opt in fil_opts.keys():
            winner  = 'def'
            winner  = 'usr' if opt in usr_opts else winner
            winner  = 'lex' if opt in lex_opts else winner
            winner  = 'fil' if opt in fil_opts else winner
            f.write(    '<tr>\n')
            f.write(    '<td>{}</td>\n'.format(opt))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='def' else 'nxt', def_opts.get(opt, '')))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='usr' else 'nxt', usr_opts.get(opt, '')))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='lex' else 'nxt', lex_opts.get(opt, '')))    if lex else None
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='fil' else 'nxt', fil_opts.get(opt, '')))
            f.write(    '<td><pre>{}</pre></td>\n'.format(cmt_opts.get(opt, '')))
            f.write(    '</tr>\n')
            def_opts.pop(opt, None)
            usr_opts.pop(opt, None)
            lex_opts.pop(opt, None)                                                                                     if lex else None
        f.write('</table><br/>\n')
        f.write('<h4>Overridden default options</h4>')
        f.write('<table>\n')
        f.write(    '<tr>\n')
        f.write(    '<th>Option name</th>\n')
        f.write(    '<th>Value in<br>default</th>\n')
        f.write(    '<th>Value in<br>user</th>\n')
        f.write(    '<th>Value in<br>{}<br></th>\n'.format(lex))                                                        if lex else None
        f.write(    '<th>Comment</th>\n')
        f.write(    '</tr>\n')
        for opt in def_opts.keys():
            winner  = 'def'
            winner  = 'usr' if opt in usr_opts else winner
            winner  = 'lex' if opt in lex_opts else winner
            winner  = 'fil' if opt in fil_opts else winner
            f.write(    '<tr>\n')
            f.write(    '<td>{}</td>\n'.format(opt))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='def' else 'nxt', def_opts.get(opt, '')))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='usr' else 'nxt', usr_opts.get(opt, '')))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='lex' else 'nxt', lex_opts.get(opt, '')))    if lex else None
            f.write(    '<td><pre>{}</pre></td>\n'.format(cmt_opts.get(opt, '')))
            f.write(    '</tr>\n')
            usr_opts.pop(opt, None)
            lex_opts.pop(opt, None)                                                                                     if lex else None
        f.write('</table><br/>\n')
        f.write('<h4>Overridden user-only options</h4>')
        f.write('<table>\n')
        f.write(    '<tr>\n')
        f.write(    '<th>Option name</th>\n')
        f.write(    '<th>Value in<br>user</th>\n')
        f.write(    '<th>Value in<br>{}</th>\n'.format(lex))                                                            if lex else None
        f.write(    '<th>Comment</th>\n')
        f.write(    '</tr>\n')
        for opt in usr_opts.keys():
            winner  = 'usr'
            winner  = 'lex' if opt in lex_opts else winner
            f.write(    '<tr>\n')
            f.write(    '<td>{}</td>\n'.format(opt))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='usr' else 'nxt', usr_opts.get(opt, '')))
            f.write(    '<td class="{}">{}</td>\n'.format('win' if winner=='lex' else 'nxt', lex_opts.get(opt, '')))    if lex else None
            f.write(    '<td><pre>{}</pre></td>\n'.format(cmt_opts.get(opt, '')))
            f.write(    '</tr>\n')
            lex_opts.pop(opt, None)                                                                                     if lex else None
        for opt in lex_opts.keys():
            winner  = 'lex'
            f.write(    '<tr>\n')
            f.write(    '<td>{}</td>\n'.format(opt))
            f.write(    '<td class="{}"></td>  \n'.format('non'))
            f.write(    '<td class="{}">{}</td>\n'.format('win', lex_opts.get(opt, '')))
            f.write(    '<td><pre>{}</pre></td>\n'.format(cmt_opts.get(opt, '')))
            f.write(    '</tr>\n')
            lex_opts.pop(opt, None)
        f.write('</table><br/>\n')
        f.write(RPT_FOOT)
        return True
   #def do_report(fn):

def get_ovrd_ed_opts(ed):
    ans     = collections.OrderedDict()
    ans['tab_size']             = ed.get_prop(app.PROP_TAB_SIZE)
    ans['tab_spaces']           = ed.get_prop(app.PROP_TAB_SPACES)
    ans['wrap_mode']            = ed.get_prop(app.PROP_WRAP)
    ans['unprinted_show']       = ed.get_prop(app.PROP_UNPRINTED_SHOW)
    ans['unprinted_spaces']     = ed.get_prop(app.PROP_UNPRINTED_SPACES)
    ans['unprinted_ends']       = ed.get_prop(app.PROP_UNPRINTED_ENDS)
    ans['unprinted_end_details']= ed.get_prop(app.PROP_UNPRINTED_END_DETAILS)
    return ans
   #def get_ovrd_ed_opts(ed):

def index_1(cllc, val, defans=-1):
    return cllc.index(val) if val in cllc else defans

if __name__ == '__main__' :     # Tests
    Command().show_dlg()    #??
        
'''
ToDo
[+][kv-kv][02apr17] History for cond
[-][kv-kv][02apr17] ? Chapters list and "chap" attr into kinfo
[-][kv-kv][02apr17] ? Tags list and "tag" attr into kinfo
[-][kv-kv][02apr17] ? Delimeter row in table
[ ][kv-kv][02apr17] "Need restart" in Comments
[+][kv-kv][02apr17] ? Calc Format by Def_val
[ ][kv-kv][02apr17] int_mm for min+max
[+][kv-kv][02apr17] VERS in Title
[+][at-kv][02apr17] 'enum' вместо 'enum_i' 
[ ][kv-kv][02apr17] Save top row in table
[+][kv-kv][03apr17] Show stat in Chap-combo and tags check-list
[-][kv-kv][03apr17] ? Add chap "(No chapter)"
[-][kv-kv][03apr17] ? Add tag "#no_tag"
[+][kv-kv][03apr17] Call opts report
[+][at-kv][04apr17] Format 'font'
[-][at-kv][04apr17] ? FilterListView
[+][at-kv][04apr17] use new default.json
[-][kv-kv][04apr17] Testing for update user.json
[+][kv-kv][04apr17] Restore Sec and Tags
[+][kv-kv][04apr17] ro-combo hitory for Tags
[+][kv-kv][05apr17] Add "default" to fonts if def_val=="default"
[+][at-kv][05apr17] Preview for format=font
[+][kv-kv][06apr17] Spec filter sign: * - to show only modified
[-][kv-kv][06apr17] Format color
[+][kv-kv][24apr17] Sort as Def or as User
[ ][kv-kv][05may17] New type "list of str"
[ ][kv-kv][23jun17] ? Filter with tag (part of tag?). "smth #my"
[ ][kv-kv][15mar18] ? Filter with all text=key+comment
[ ][kv-kv][19mar18] ? First "+" to filter with comment
[ ][kv-kv][19mar18] Point the fact if value is overed in ed
[ ][kv-kv][20mar18] Allow to add/remove opt in user/lex
[ ][kv-kv][21mar18] ? Allow to meta keys in user.json: 
                        "_fif_LOG__comment":"Comment for fif_LOG"
[ ][kv-kv][22mar18] Set conrol's tab_order to always work Alt+E for "Valu&e"
[ ][kv-kv][26mar18] Use editor for comment
[ ][kv-kv][26mar18] Increase w for one col when user increases w of dlg (if no h-scroll)
'''