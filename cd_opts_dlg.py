''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '2.2.02 2018-05-14'
ToDo: (see end of file)
'''

import  re, os, sys, json, collections, itertools, webbrowser, tempfile, html, pickle, time, datetime
from    itertools       import *
from pathlib import PurePath as PPath
from pathlib import     Path as  Path
def first_true(iterable, default=False, pred=None):return next(filter(pred, iterable), default) # 10.1.2. Itertools Recipes

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
pass;                           pf80=lambda d:pformat(d,width=80)
pass;                           pf60=lambda d:pformat(d,width=60)
pass;                           ##!! waits correction

_   = get_translation(__file__) # I18N

MIN_API_VER     = '1.0.168'
MIN_API_VER_4WR = '1.0.175'     # vis
MIN_API_VER     = '1.0.231'     # listview has prop columns
MIN_API_VER     = '1.0.236'     # p, panel
MIN_API_VER     = '1.0.237'     # STATUSBAR_SET_CELL_HINT
VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')
MAX_HIST    = apx.get_opt('ui_max_history_edits', 20)
CFG_JSON    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_options_editor.json'
HTM_RPT_FILE= str(Path(tempfile.gettempdir()) / 'CudaText_option_report.html')
FONT_LST    = ['default'] \
            + [font 
                for font in app.app_proc(app.PROC_ENUM_FONTS, '')
                if not font.startswith('@')] 
pass;                          #FONT_LST=FONT_LST[:3]

def load_definitions(defn_path:Path)->list:
    """ Return  
            [{  opt:'opt name'
            ,   def:<def val>
            ,   cmt:'full comment'
            ,   frm:'bool'|'float'|'int'|'int2s'|'str'|'strs'|'str2s'|'font'|'font-e'|'hotk'|'file'|'json'      |'unk'
            ,   lst:[str]       for frm==ints
            ,   dct:[(num,str)] for frm==int2s
            ,       [(str,str)] for frm==str2s
            ,   chp:'chapter/chapter'
            ,   tgs:['tag',]
            }]
    """
    pass;                      #LOG and log('defn_path={}',(defn_path))
    kinfs   = []
    lines   = defn_path.open(encoding='utf8').readlines()
    if lines[0][0]=='[':
        # Data is ready - SKIP parsing
        kinfs   = json.loads(defn_path.open(encoding='utf8').read(), object_pairs_hook=odict)
        for kinf in kinfs:
            pass;              #LOG and log('opt in kinf={}',('opt' in kinf))
            if isinstance(kinf['cmt'], list):
                kinf['cmt'] = '\n'.join(kinf['cmt'])

        upd_cald_vals(kinfs, '+def')
        for kinf in kinfs:
            kinf['jdc'] = kinf.get('jdc', kinf.get('dct', []))
            kinf['jdf'] = kinf.get('jdf', kinf.get('def', ''))
        return kinfs

    l       = '\n'
    
    #NOTE: parse_raw
    reTags  = re.compile(r' *\((#\w+,?)+\)')
    reN2S   = re.compile(r'^\s*(\d+): *(.+)'    , re.M)
    reS2S   = re.compile(r'^\s*"(\w*)": *(.+)'  , re.M)
#   reLike  = re.compile(r' *\(like (\w+)\)')               ##??
    reFldFr = re.compile(r'\s*Folders from: (.+)')
    def parse_cmnt(cmnt, frm):#, kinfs):  
        tags= set()
        mt  = reTags.search(cmnt)
        while mt:
            tags_s  = mt.group(0)
            tags   |= set(tags_s.strip(' ()').replace('#', '').split(','))
            cmnt    = cmnt.replace(tags_s, '')
            mt      = reTags.search(cmnt)
        dctN= [[int(m.group(1)), m.group(2).rstrip(', ')] for m in reN2S.finditer(cmnt+l)]
        dctS= [[    m.group(1) , m.group(2).rstrip(', ')] for m in reS2S.finditer(cmnt+l)]
#       frmK,\
#       dctK= frm, None
#       mt  = reLike.search(cmnt)
#       if mt:
#           ref_knm = mt.group(1)
#           ref_kinf= [kinf for kinf in kinfs if kinf['key']==ref_knm]
#           if not ref_kinf:
#               log('Error on parse {}. No ref-key {} from comment\n{}',(path_to_raw, ref_knm, cmnt))
#           else:
#               ref_kinf = ref_kinf[0]
#               frmK= ref_kinf['format']    if 'format' in ref_kinf else    frmK
#               dctK= ref_kinf['dct']       if 'dct'    in ref_kinf else    dctK
        lstF= None
        mt  = reFldFr.search(cmnt)
        if mt:
            from_short  = mt.group(1)
            from_dir    = from_short if os.path.isabs(from_short) else os.path.join(app.app_path(app.APP_DIR_DATA), from_short)
            pass;              #LOG and log('from_dir={}',(from_dir))
            if not os.path.isdir(from_dir):
                log(_('No folder "{}" from\n{}'), from_short, cmnt)
            else:
                lstF    = [d for d in os.listdir(from_dir) if os.path.isdir(from_dir+os.sep+d) and d.strip()]
                lstF    = sorted(lstF)
                pass;          #LOG and log('lstF={}',(lstF))
        frm,\
        lst = ('strs' , lstF)    if lstF else \
              (frm    , []  )
        frm,\
        dct = ('int2s', dctN)    if dctN else \
              ('str2s', dctS)    if dctS else \
              (frm    , []  )
#             (frmK   , dctK)    if dctK else 
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
    pre_cmnt= ''
    pre_kinf= None
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
            
            cmnt    = cmnt.strip(l)     if cmnt else pre_cmnt
            ref_frm = cmnt[:3]=='...'
            pre_cmnt= cmnt              if cmnt else pre_cmnt
            pass;              #LOG and log('ref_frm,pre_cmnt,cmnt={}',(ref_frm,pre_cmnt,cmnt))
            cmnt    = cmnt.lstrip('.'+l)

            dfrm    = 'font-e' if dfrm=='font' and 'Empty string is allowed' in cmnt   else dfrm
            
            kinf    = odict()
            kinfs  += [kinf]
            kinf['opt']         = key
            kinf['def']         = dval
            kinf['cmt']         = cmnt.strip()
            kinf['frm']         = dfrm
            if dfrm in ('int','str'):
                cmnt,frm,\
                dct,lst,tags    = parse_cmnt(cmnt, dfrm)#, kinfs)
                kinf['cmt']     = cmnt.strip()
                if frm!=dfrm:
                    kinf['frm'] = frm
                if dct:
                    kinf['dct'] = dct
                if lst:
                    kinf['lst'] = lst
                if tags:
                    kinf['tgs'] = tags
            if dfrm=='font':
                kinf['lst']     = FONT_LST
            if dfrm=='font-e':
#               kinf['lst']     = FONT_LST + ['']
                kinf['lst']     = [''] + FONT_LST
            if chap:
                kinf['chp']     = chap
            
            if ref_frm and pre_kinf:
                # Copy frm data from prev oi
                pass;          #LOG and log('Copy frm pre_kinf={}',(pre_kinf))
                kinf[    'frm'] = pre_kinf['frm']
                if 'dct' in pre_kinf:
                    kinf['dct'] = pre_kinf['dct']
                if 'lst' in pre_kinf:
                    kinf['lst'] = pre_kinf['lst']
            
            pre_kinf= kinf.copy()
            cmnt    = ''
       #for line
    upd_cald_vals(kinfs, '+def')
    for kinf in kinfs:
        kinf['jdc'] = kinf.get('jdc', kinf.get('dct', []))
        kinf['jdf'] = kinf.get('jdf', kinf.get('def', ''))
    return kinfs
   #def load_definitions

def load_vals(opt_dfns:list, lexr_json='', ed_=None, full=False)->odict:
    """ Create reformated copy (as odict) of 
            definitions data opt_dfns (see load_definitions) 
        If ed_ then add
            'fval' 
            for some options
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
        ?   ,   fval:<value from ed>
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
        pass;                  #LOG and log('no lexr_json={}',(lexr_json))
#   edit_vals       = get_ovrd_ed_opts(ed)
    pass;                      #LOG and log('lexr_vals={}',(lexr_vals))

    # Fill vals for defined opt
    pass;                      #LOG and log('no opt={}',([oi for oi in opt_dfns if 'opt' not in oi]))
    oinf_valed  = odict([(oi['opt'], oi) for oi in opt_dfns])
    for opt, oinf in oinf_valed.items():
        if opt in user_vals:                # Found user-val for defined opt
            oinf['uval']    = user_vals[opt]
        if opt in lexr_vals:                # Found lexer-val for defined opt
            oinf['lval']    = lexr_vals[opt]
        if ed_ and opt in apx.OPT2PROP:     # Found file-val for defined opt
            fval            = ed_.get_prop(apx.OPT2PROP[opt])
#           if fval == oinf.get('lval', oinf.get('uval', oinf.get('def'))): continue    # No overwrite
            oinf['fval']    =fval
#       if opt in edit_vals:        # Found file-val for defined opt
#           oinf['fval']    = edit_vals[opt]

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
            pass;              #LOG and log('oi={}',(oi))


    # Fill calculated attrs
    if not what or '+clcd' in what:
        for op, oi in ois.items():
            oi['!']     =( '+!!' if 'def' not in oi and 'lval' in oi   else
                            '+!' if 'def' not in oi and 'uval' in oi   else
                           '!!!' if                     'fval' in oi 
                                    and oi['fval'] != oi.get('lval'
                                                    , oi.get('uval'
                                                    , oi.get( 'def'))) else
                            '!!' if                     'lval' in oi   else
                             '!' if                     'uval' in oi   else
                          '')
            dct         = odict(oi.get('dct', []))
            oi['juvl']  = oi.get('uval', '') \
                            if not dct or 'uval' not in oi else \
                          f('({}) {}', oi['uval'], dct[oi['uval']])
            oi['jlvl']  = oi.get('lval', '') \
                            if not dct or 'lval' not in oi else \
                          f('({}) {}', oi['lval'], dct[oi['lval']])
            oi['jfvl']  = oi.get('fval', '') \
                            if not dct or 'fval' not in oi else \
                          f('({}) {}', oi['fval'], dct[oi['fval']])
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
    COL_FIL = 6
    COL_NMS = (_('Section'), _('Option'), '!', _('Default'), ('User'), _('Lexer'), _('File "{}"'))
    COL_MWS = [   70,           150,       25,    120,         120,       70,         50]   # Min col widths
    COL_N   = len(COL_MWS)
    CMNT_MHT= 60                            # Min height of Comment
    STBR_FLT= 10
    STBR_ALL= 11
    STBR_MSG= 12
    STBR_H  = apx.get_opt('ui_statusbar_height',24)

    FILTER_C= _('&Filter')
    NO_CHAP = _('_no_')
    CHPS_H  = f(_('Choose section to append in "{}"'), FILTER_C).replace('&', '')
    FLTR_H  = _('Suitable options will contain all specified words.'
              '\r Tips and tricks:'
              '\r • Add "#" to search the words also in comments.'
              '\r • Add "@sec" to show options from section with "sec" in name.'
              '\r • To show only overridden options:'
              '\r   - Add "!"   to show only User+Lexer+File.'
              '\r   - Add "!!"  to show only Lexer+File'
              '\r   - Add "!!!" to show only File.'
              '\r • Use "<" or ">" for word boundary.'
              '\r     Example: '
              '\r       size> <tab'
              '\r     selects "tab_size" but not "ui_tab_size" or "tab_size_x".'
              '\r • Alt+L - Clear filter')
    LOCV_C  = _('Go to "{}" in user/lexer config file')
    LOCD_C  = _('Go to "{}" in default config file')
    TOOP_H  = f(_('Close dialog and open user/lexer settings file'
                  '\rto edit the current option.'
                  '\rSee also menu command'
                  '\r   {}'), f(LOCD_C, '<option>'))

    
    def __init__(self
        , path_keys_info    =''             # default.json or parsed data
        , subset            =''             # To get/set from/to cuda_options_editor.json
        , how               ={}             # Details to work
        ):
        M,m         = OptEdD,self
        
        m.ed        = ed
        m.how       = how
        
        m.defn_path = Path(path_keys_info)
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
        
        m.cur_op    = m.stores.get(m.subset+'cur_op'    , '')           # Name of current option
        m.col_ws    = m.stores.get(m.subset+'col_ws'    , M.COL_MWS[:])
        m.col_ws    = m.col_ws if M.COL_N==len(m.col_ws) else M.COL_MWS[:]
        m.h_cmnt    = m.stores.get(m.subset+'cmnt_heght', M.CMNT_MHT)
        m.sort      = m.stores.get(m.subset+'sort'      , (-1, True))   # Def sort is no sort
        m.live_fltr = m.stores.get(m.subset+'live_fltr' , False)        # To filter after each change and no History
        m.cond_hl   = [s for s in m.stores.get(m.subset+'h.cond', []) if s] if not m.live_fltr else []
        m.cond_s    = ''        # String filter
        m.ops_only  = []        # Subset to show (future)
        
        m.lexr      = m.ed.get_prop(app.PROP_LEXER_CARET)
        m.all_ops   = m.stores.get(m.subset+'all_ops'   , False)        # Show also options without definition

        m.opts_defn = {}        # Meta-info for options: format, comment, dict of values, chapter, tags
        m.opts_full = {}        # Show all options
        m.chp_tree  = {}        # {'Ui':{ops:[], 'kids':{...}, 'path':'Ui/Tabs'}
        m.pth2chp   = {}        # path-index for m.chp_tree

        # Cache
        m.SKWULFs   = []        # Last filtered+sorted
        m.cols      = []        # Last info about listview columns
        m.itms      = []        # Last info about listview cells
        
#       m.bk_files  = {}
#       m.do_file('backup-user')    if m.bk_sets else 0
        
        m.do_file('load-data')
        
        m.for_ulf   = 'u'       # 'u' for User, 'l' for Lexer, 'f' for File
        m.cur_op    = m.cur_op if m.cur_op in m.opts_full else ''           # First at start
#       m.cur_op    = list(m.opts_full.keys())[0] if m.opts_full else ''    # First at start
        m.cur_in    = 0 if m.cur_op else -1
        
        m.stbr      = None      # Handle for statusbar_proc
        m.locate_on_exit    = None
        
        m.chng_rpt  = []        # Report of all changes by user
        m.apply_one = m.stores.get(m.subset+'apply_one', False) # Do one call OpsReloadAndApply on exit
        m.apply_need= False                                     # Need to call OpsReloadAndApply
        m.auto4file = m.stores.get(m.subset+'auto4file', True)  # Auto reset file value to over value def/user/lex
       #def __init__
    
    def stbr_act(self, tag=None, val='', opts={}):
        M,m = OptEdD,self
        if not m.stbr:  return 
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_TEXT, tag=tag, value=str(val))
       #def stbr_act
    
    def do_file(self, what, data='', opts={}):
        M,m = OptEdD,self
        if False:pass
        elif what=='load-data':
            pass;              #LOG and log('',)
            m.opts_defn = load_definitions(m.defn_path)
            pass;              #LOG and log('m.opts_defn={}',pf([o for o in m.opts_defn]))
            pass;              #LOG and log('m.opts_defn={}',pf([o for o in m.opts_defn if '2s' in o['frm']]))
            m.opts_full = load_vals(m.opts_defn, 'lexer '+m.lexr+'.json', m.ed, m.all_ops)
            m.cur_op    = m.cur_op if m.cur_op in m.opts_full else ''
            pass;              #LOG and log('m.opts_full={}',pf(m.opts_full))
            m.do_file('build-chp-tree')
        
        elif what=='build-chp-tree':
            # Build chapter tree
            m.chp_tree  = odict(ops=list(m.opts_full.keys())
                               ,kids=odict()
                               ,path='')  # {chp:{ops:[], kids:{...}, path:'c1/c2'}
            m.pth2chp   = {}                                    # {path:chp}
            for op,oi in m.opts_full.items():
                chp_s   = oi.get('chp', M.NO_CHAP)
                chp_s   = chp_s if chp_s else M.NO_CHAP
                chp_node= m.chp_tree                            # Start root to move
                kids    = chp_node['kids']
                path    =''
                for chp in chp_s.split('/'):
                    # Move along branch and create nodes if need
                    chp_node    = kids.setdefault(chp, odict())
                    path       += ('/'+chp) if path else chp
                    chp_node['path']= path
                    m.pth2chp[path] = chp_node
                    ops_l       = chp_node.setdefault('ops', [])
                    ops_l      += [op]
                    if not ('/'+chp_s).endswith('/'+chp):   # not last
                        kids    = chp_node.setdefault('kids', odict())
            pass;              #LOG and log('m.chp_tree=¶{}',pf60(m.chp_tree))
            pass;              #LOG and log('m.pth2chp=¶{}',pf60(m.pth2chp))
        
        elif what == 'locate_to':
            to_open = data['path']
            find_s  = data['find']
            app.file_open(to_open)      ##!!
            pass;               log('to_open={}',(to_open))
            pass;               log('ed.get_filename()={}',(ed.get_filename()))
            m.ag.opts['on_exit_focus_to_ed'] = ed
#           ed_to_fcs   = m.ag.opts['on_exit_focus_to_ed'] = ed_of_file_open(to_open)
#           ed_to_fcs.focus()
            # Locate
            user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
#           pass;               log('ed_to_fcs.get_filename()={}',(ed_to_fcs.get_filename()))
#           pass;               log('ed.get_filename()={}',(ed.get_filename()))
            pass;              #LOG and log('find_s={!r}',(find_s))
            ed.cmd(cmds.cmd_FinderAction, chr(1).join(['findnext', find_s, '', 'fa']))    # f - From-caret,  a - Wrap
            app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)
            
        elif what in ('locate-def', 'locate-opt', 'goto-def', 'goto-opt', ):
            if not m.cur_op:
                m.stbr_act(M.STBR_MSG, _('Choose option to find in config file'))
                return False
            oi      = m.opts_full[m.cur_op]
            pass;              #LOG and log('m.cur_op,oi={}',(m.cur_op,oi))
            to_open = ''
            if what in ('locate-opt', 'goto-opt'):
                if 'uval' not in oi and m.for_ulf=='u':
                    m.stbr_act(M.STBR_MSG, f(_('No user value for option "{}"'), m.cur_op))
                    return False
                if 'lval' not in oi and m.for_ulf=='l':
                    m.stbr_act(M.STBR_MSG, f(_('No lexer "{}" value for option "{}"'), m.lexr, m.cur_op))
                    return False
                to_open = 'lexer '+m.lexr+'.json'   if m.for_ulf=='l' else 'user.json'
                to_open = app.app_path(app.APP_DIR_SETTINGS)+os.sep+to_open
            else:
                if 'def' not in oi:
                    m.stbr_act(M.STBR_MSG, f(_('No default for option "{}"'), m.cur_op))
                    return False
                to_open = str(m.defn_path)
            if not os.path.exists(to_open):
                log('No file={}',(to_open))
                return False

            find_s  = f('"{}"', m.cur_op)
            if what in ('goto-def', 'goto-opt'):
                m.locate_on_exit  = d(path=to_open, find=find_s)
                return True #
            m.do_file('locate_to',  d(path=to_open, find=find_s))
            return False
        
       #elif what=='set-dfns':
       #    m.defn_path = data
       #    m.do_file('load-data')
       #    return d(ctrls=odict(m.get_cnts('lvls')))
        
        elif what=='set-lexr':
            m.opts_full = load_vals(m.opts_defn, 'lexer '+m.lexr+'.json', m.ed, m.all_ops)
            return d(ctrls=odict(m.get_cnts('lvls')))

        elif what=='out-rprt':
            if do_report(HTM_RPT_FILE, 'lexer '+m.lexr+'.json', m.ed):
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
        M,m = OptEdD,self
        if opts=='key2ind':
            opt_nm  = nm if nm else m.cur_op
            m.cur_in= index_1([m.SKWULFs[row][1] for row in range(len(m.SKWULFs))], opt_nm, -1)
            return m.cur_in
        
        if opts=='ind2key':
            opt_in  = ind if -1!=ind else m.ag.cval('lvls')
            m.cur_op= m.SKWULFs[opt_in][1] if -1<opt_in<len(m.SKWULFs) else ''
            return m.cur_op
        
        if opts=='fid4ed':
            if not m.cur_op:    return 'lvls'
            frm = m.opts_full[m.cur_op]['frm']
            fid =   'eded'  if frm in ('str', 'int', 'float')                       else \
                    'edcb'  if frm in ('int2s', 'str2s', 'strs', 'font', 'font-e')  else \
                    'edrf'  if frm in ('bool',)                                     else \
                    'brow'  if frm in ('hotk', 'file')                              else \
                    'toop'  if frm in ('json')                                      else \
                    'lvls'
            pass;              #LOG and log('m.cur_op,frm,fid={}',(m.cur_op,frm,fid))
            return fid
        
        pass;                  #LOG and log('m.cur_op, m.lexr={}',(m.cur_op, m.lexr))
        vis,ens,vas,its = {},{},{},{}
        
        ens['eded'] = ens['setd']                                                   = False # All un=F
        vis['eded'] = vis['edcb']=vis['edrf']=vis['edrt']=vis['brow']=vis['toop']   = False # All vi=F
        vas['eded'] = vas['dfvl']=vas['cmnt']= ''                                           # All ed empty
        vas['edcb'] = -1
        vas['edrf'] = vas['edrt'] = False
        its['edcb'] = []
        
        ens['dfvl']         = True
        ens['tofi']         = m.cur_op in apx.OPT2PROP
        if m.for_ulf=='l' and m.lexr not in m.lexr_l:
            # Not selected lexer
            vis['eded']     = True
            ens['dfvl']     = False
            return vis,ens,vas,its
        
        if m.for_ulf=='f' and m.cur_op not in apx.OPT2PROP:
            # No the option for File
            vis['eded']     = True
            ens['dfvl']     = False
            return vis,ens,vas,its
        
        if not m.cur_op:
            # No current option
            vis['eded']     = True
        else:
            # Current option
            oi              = m.opts_full[m.cur_op]
            pass;              #LOG and log('oi={}',(oi))
            vas['dfvl']     = str(oi.get('jdf' , '')).replace('True', 'true').replace('False', 'false')
            vas['uval']     = oi.get('uval', '')
            vas['lval']     = oi.get('lval', '')
            vas['fval']     = oi.get('fval', '')
            vas['cmnt']     = oi.get('cmt' , '')
            frm             = oi['frm']
            ulfvl_va        = vas['fval'] \
                                if m.for_ulf=='f' else \
                              vas['lval'] \
                                if m.for_ulf=='l' else \
                              vas['uval']                       # Cur val with cur state of "For lexer"
            ens['eded']     = frm not in ('json', 'hotk', 'file')
            ens['setd']     = frm not in ('json',) and ulfvl_va is not None
            if False:pass
            elif frm in ('json'):
                vis['toop'] = True
                vis['eded'] = True
                vas['eded'] = str(ulfvl_va)
            elif frm in ('str', 'int', 'float'):
                vis['eded'] = True
                vas['eded'] = str(ulfvl_va)
            elif frm in ('hotk', 'file'):
                vis['eded'] = True
                vis['brow'] = True
                vas['eded'] = str(ulfvl_va)
            elif frm in ('bool',):
                vis['edrf'] = True
                vis['edrt'] = True
                vas['edrf'] = ulfvl_va==False
                vas['edrt'] = ulfvl_va==True
            elif frm in ('int2s', 'str2s'):
                vis['edcb'] = True
                ens['edcb'] = True
                its['edcb'] = oi['jdc']
                vas['edcb'] = index_1([k for (k,v) in oi['dct']], ulfvl_va, -1)
                pass;          #LOG and log('ulfvl_va, vas[edcb]={}',(ulfvl_va,vas['edcb']))
            elif frm in ('strs','font','font-e'):
#           elif frm in ('strs',):
                vis['edcb'] = True
                ens['edcb'] = True
                its['edcb'] = oi['lst']
                vas['edcb'] = index_1(oi['lst'], ulfvl_va, -1)
        
        pass;                  #LOG and log('ulfvl_va={}',(ulfvl_va))
        pass;                  #LOG and log('vis={}',(vis))
        pass;                  #LOG and log('ens={}',(ens))
        pass;                  #LOG and log('vas={}',(vas))
        pass;                  #LOG and log('its={}',(its))
        return vis,ens,vas,its
       #def _prep_opt

    def show(self
        , title                     # For cap of dlg
        ):
        M,m = OptEdD,self
#       pass;                   return

        def when_exit(ag):
            pass;              #LOG and log('',())
            pass;              #pr_   = dlg_proc_wpr(ag.id_dlg, app.DLG_CTL_PROP_GET, name='edch')
            pass;              #log('exit,pr_={}',('edch', {k:v for k,v in pr_.items() if k in ('x','y')}))
            pass;              #log('cols={}',(ag.cattr('lvls', 'cols')))
            m.col_ws= [ci['wd'] for ci in ag.cattr('lvls', 'cols')]
            m.stores[m.subset+'cmnt_heght'] = m.ag.cattr('cmnt', 'h')
            
            if m.apply_one and m.apply_need:
                ed.cmd(cmds.cmd_OpsReloadAndApply)
            
            if m.locate_on_exit:
                m.do_file('locate_to', m.locate_on_exit)
           #def when_exit

        m.dlg_min_w = 10 + sum(M.COL_MWS) + M.COL_N + M.SCROLL_W
        m.dlg_w     = 10 + sum(m.col_ws)  + M.COL_N + M.SCROLL_W
        m.dlg_h     = 270 + m.h_cmnt    +10 + M.STBR_H
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
                                   #'gen_repro_to_file':'repro_dlg_opted.py',    #NOTE: repro
                                }
        )
#       m.bte_mn= app.dlg_proc(m.ag.id_dlg, app.DLG_CTL_HANDLE, name='men_')
#       app.button_proc(m.bte_mn, app.BTN_SET_FLAT, True)

        m.stbr  = app.dlg_proc(m.ag.id_dlg, app.DLG_CTL_HANDLE, name='stbr')
        app.statusbar_proc(m.stbr, app.STATUSBAR_ADD_CELL               , tag=M.STBR_ALL)
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_SIZE          , tag=M.STBR_ALL, value=40)
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_ALIGN         , tag=M.STBR_ALL, value='R')
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_HINT          , tag=M.STBR_ALL, value=_('Number of all options'))
        app.statusbar_proc(m.stbr, app.STATUSBAR_ADD_CELL               , tag=M.STBR_FLT)
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_SIZE          , tag=M.STBR_FLT, value=40)
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_ALIGN         , tag=M.STBR_FLT, value='R')
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_HINT          , tag=M.STBR_FLT, value=_('Number of shown options'))
        app.statusbar_proc(m.stbr, app.STATUSBAR_ADD_CELL               , tag=M.STBR_MSG)
        app.statusbar_proc(m.stbr, app.STATUSBAR_SET_CELL_AUTOSTRETCH   , tag=M.STBR_MSG, value=True)
        m.stbr_act(M.STBR_ALL, len(m.opts_full))
        m.stbr_act(M.STBR_FLT, len(m.opts_full))

        m.ag.show(when_exit)
        m.ag    = None

        # Save for next using
        m.stores[m.subset+'cur_op']     = m.cur_op
        m.stores[m.subset+'col_ws']     = m.col_ws
        m.stores[m.subset+'sort']       = m.sort
        if not m.live_fltr:
            m.stores[m.subset+'h.cond'] = m.cond_hl
        m.stores[m.subset+'all_ops']    = m.all_ops
        open(CFG_JSON, 'w').write(json.dumps(m.stores, indent=4))
       #def show
    
    def get_cnts(self, what=''):
        M,m = OptEdD,self
        
        reNotWdChar = re.compile(r'\W')
        def test_fltr(fltr_s, op, oi):
            if not fltr_s:                                  return True
            pass;              #LOG and log('fltr_s, op, oi[!]={}',(fltr_s, op, oi['!']))
            if '!!!' in fltr_s and '!!!' not in oi['!']:    return False
            if '!!'  in fltr_s and '!!'  not in oi['!']:    return False
            pass;              #LOG and log('skip !!',())
            if  '!'  in fltr_s and  '!'  not in oi['!']:    return False
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
            return all(map(lambda c:c in text, fltr_s.split()))
           #def test_fltr

        def get_tbl_cols(opts_full, SKWULFs, sort, col_ws):
            cnms    = list(M.COL_NMS)
            cnms[M.COL_FIL] = f(cnms[M.COL_FIL], m.ed.get_prop(app.PROP_TAB_TITLE))
            sort_cs = ['' if c!=sort[0] else '↑ ' if sort[1] else '↓ ' for c in range(M.COL_N)] # ▲ ▼ ?
            cols    = [  d(nm=sort_cs[0]+cnms[0], wd=col_ws[0] ,mi=M.COL_MWS[0])
                        ,d(nm=sort_cs[1]+cnms[1], wd=col_ws[1] ,mi=M.COL_MWS[1])
                        ,d(nm=sort_cs[2]+cnms[2], wd=col_ws[2] ,mi=M.COL_MWS[2]   ,al='C')
                        ,d(nm=sort_cs[3]+cnms[3], wd=col_ws[3] ,mi=M.COL_MWS[3])
                        ,d(nm=sort_cs[4]+cnms[4], wd=col_ws[4] ,mi=M.COL_MWS[4])
                        ,d(nm=sort_cs[5]+cnms[5], wd=col_ws[5] ,mi=M.COL_MWS[5])
                        ,d(nm=sort_cs[6]+cnms[6], wd=col_ws[6] ,mi=M.COL_MWS[6])
                        ]
            return cols
           #def get_tbl_cols
        
        def get_tbl_data(opts_full, cond_s, ops_only, sort, col_ws):
            # Filter table data
            pass;              #LOG and log('cond_s={}',(cond_s))
            chp_cond    = ''
            chp_no_c    = False
            if  '@' in cond_s:
                # Prepare to match chapters
                chp_cond    = ' '.join([mt.group(1) for mt in re.finditer(r'@([\w/]+)'    , cond_s)]).upper()   # @s+ not empty chp
                chp_cond    = chp_cond.replace(M.NO_CHAP.upper(), '').strip()
                chp_no_c    = '@'+M.NO_CHAP in cond_s
                cond_s      =                                 re.sub(     r'@([\w/]*)', '', cond_s)             # @s* clear @ and cph
            pass;              #LOG and log('chp_cond, chp_no_c, cond_s={}',(chp_cond, chp_no_c, cond_s))
            SKWULFs  = [  (oi.get('chp','') 
                         ,op
                         ,oi['!']
                         ,str(oi.get('jdf' ,'')).replace('True', 'true').replace('False', 'false')
                         ,str(oi.get('juvl','')).replace('True', 'true').replace('False', 'false')
                         ,str(oi.get('jlvl','')).replace('True', 'true').replace('False', 'false')
                         ,str(oi.get('jfvl','')).replace('True', 'true').replace('False', 'false')
                         ,oi['frm']
                         )
                            for op,oi in opts_full.items()
                            if  (not chp_cond   or chp_cond in oi.get('chp', '').upper())
                            and (not chp_no_c   or not oi.get('chp', ''))
                            and (not cond_s     or test_fltr(cond_s, op, oi))
                            and (not ops_only   or op in ops_only)
                      ]
            # Sort table data
            if -1 != sort[0]:     # With sort col
                prfx0       = '0' if sort[1] else '1'
                prfx1       = '1' if sort[1] else '0'
                SKWULFs     = sorted(SKWULFs
                               ,key=lambda it:((prfx1 if it[sort[0]] else prfx0)+it[sort[0]])   # To show empty in bottom
                               ,reverse=sort[1])
            # Fill table
            pass;              #LOG and log('M.COL_NMS,col_ws,M.COL_MWS={}',(len(M.COL_NMS),len(col_ws),len(M.COL_MWS)))
            cols    = get_tbl_cols(opts_full, SKWULFs, sort, col_ws)

            itms    = (list(zip([_('Section'),_('Option'), '', _('Default'), _('User'), _('Lexer'), _('File')], map(str, col_ws)))
                     #,         [ (str(n)+':'+sc,k         ,w    ,dv           ,uv         ,lv          ,fv)    # for debug
                     #,         [ (sc+' '+fm    ,k         ,w    ,dv           ,uv         ,lv          ,fv)    # for debug
                      ,         [ (sc           ,k         ,w    ,dv           ,uv         ,lv          ,fv)    # for user
                        for  n,(   sc           ,k         ,w    ,dv           ,uv         ,lv          ,fv, fm) in enumerate(SKWULFs) ]
#                       for  (     sc           ,k         ,w    ,dv           ,uv         ,lv          ,fv, fm) in SKWULFs ]
                      )
            return SKWULFs, cols, itms
           #def get_tbl_data
           
        if not what or '+lvls' in what:
            m.SKWULFs,\
            m.cols  ,\
            m.itms  = get_tbl_data(m.opts_full, m.cond_s, m.ops_only, m.sort, m.col_ws)
            if 'stbr' in dir(m):
                m.stbr_act(M.STBR_FLT, len(m.SKWULFs))

        if '+cols' in what:
            pass;              #LOG and log('m.col_ws={}',(m.col_ws))
            m.cols  = get_tbl_cols(m.opts_full, m.SKWULFs, m.sort, m.col_ws)
            pass;              #LOG and log('m.cols={}',(m.cols))
        
        # Prepare [Def]Val data by m.cur_op
        vis,ens,vas,its = m._prep_opt()
        
        ed_s_c  = _('>Fil&e:')  if m.for_ulf=='f' else \
                  _('>L&exer:') if m.for_ulf=='l' else \
                  _('>Us&er:')
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

        tofi_en = not m.how.get('only_for_ul', not ens['tofi'])         # Forbid to switch fo File ops
        if '+cur' in what:
            cnts   += [0
            ,('ed_s',d(cap=ed_s_c                       ,hint=m.cur_op      ))
            ,('eded',d(vis=vis['eded'],en=ens['eded']                       ))
            ,('edcb',d(vis=vis['edcb']                  ,items=its['edcb']  ))
            ,('edrf',d(vis=vis['edrf']                                      ))
            ,('edrt',d(vis=vis['edrt']                                      ))
            ,('brow',d(vis=vis['brow']                                      ))
            ,('toop',d(vis=vis['toop']                                      ))
            ,('dfv_',d(                                  hint=m.cur_op      ))
            ,('dfvl',d(                en=ens['dfvl']                       ))
            ,('setd',d(                en=ens['setd']                       ))
            ,('tofi',d(                en=tofi_en                           ))
            ][1:]

        if what and cnts:
            # Part info
            return cnts

        # Full dlg controls info    #NOTE: cnts
        cmnt_t  = m.dlg_h-m.h_cmnt-5-M.STBR_H
        tofi_c  = m.ed.get_prop(app.PROP_TAB_TITLE)
        cnts    = [0                                                                                                                        #
    # Hidden buttons                                                                                                                    
 ,('flt-',d(tp='bt' ,cap='&l'   ,sto=False              ,t=0,l=0,w=0))  # &l
 ,('fltr',d(tp='bt' ,cap=''     ,sto=False  ,def_bt='1' ,t=0,l=0,w=0))  # Enter
 ,('srt0',d(tp='bt' ,cap='&1'   ,sto=False              ,t=0,l=0,w=0))  # &1
 ,('srt1',d(tp='bt' ,cap='&2'   ,sto=False              ,t=0,l=0,w=0))  # &2
 ,('srt2',d(tp='bt' ,cap='&3'   ,sto=False              ,t=0,l=0,w=0))  # &3
 ,('srt3',d(tp='bt' ,cap='&4'   ,sto=False              ,t=0,l=0,w=0))  # &4
 ,('srt4',d(tp='bt' ,cap='&5'   ,sto=False              ,t=0,l=0,w=0))  # &5
 ,('srt5',d(tp='bt' ,cap='&6'   ,sto=False              ,t=0,l=0,w=0))  # &6
 ,('srt6',d(tp='bt' ,cap='&7'   ,sto=False              ,t=0,l=0,w=0))  # &7
 ,('cws-',d(tp='bt' ,cap='&W'   ,sto=False              ,t=0,l=0,w=0))  # &w
 ,('cpnm',d(tp='bt' ,cap='&C'   ,sto=False              ,t=0,l=0,w=0))  # &c
 ,('erpt',d(tp='bt' ,cap='&O'   ,sto=False              ,t=0,l=0,w=0))  # &o
 ,('apnw',d(tp='bt' ,cap='&Y'   ,sto=False              ,t=0,l=0,w=0))  # &y
 ,('help',d(tp='bt' ,cap='&H'   ,sto=False              ,t=0,l=0,w=0))  # &h
    # Top-panel                                                                                                             
 ,('ptop',d(tp='pn' ,h=    270 ,w=m.dlg_w               ,ali=ALI_CL                                                         
                    ,h_min=270                                                                                                  ))
    # Menu                                                                                                                      
 ,('menu',d(tp='bt' ,tid='cond' ,l=-30-5,w=  30 ,p='ptop'   ,cap='&='                                               ,a='LR'     ))  # &=
    # Filter                                                                                                                    
 ,('chps',d(tp='bt' ,tid='cond' ,l=-270 ,r=-180 ,p='ptop'   ,cap=_('+&Section…')    ,hint=M.CHPS_H                  ,a='LR'     ))  # &s
 ,('flt_',d(tp='lb' ,tid='cond' ,l=   5 ,w=  70 ,p='ptop'   ,cap='>'+M.FILTER_C+':' ,hint=M.FLTR_H                              ))  # &f
 ,('cond',d(tp='cb' ,t=  5      ,l=  78 ,r=-270 ,p='ptop'   ,items=m.cond_hl                                        ,a='lR'     ))  #
    # Table of keys+values                                                                                                  
 ,('lvls',d(tp='lvw',t= 35,h=160,l=   5 ,r=  -5 ,p='ptop'   ,items=m.itms,cols=m.cols   ,grid='1'                   ,a='tBlR'   ))  #
    # Editors for value                                                                                                         
 ,('ed_s',d(tp='lb' ,t=210      ,l=   5 ,w=  70 ,p='ptop'   ,cap=ed_s_c             ,hint=m.cur_op                  ,a='TB'     ))  # &e 
 ,('eded',d(tp='ed' ,tid='ed_s' ,l=  78 ,r=-270 ,p='ptop'                           ,vis=vis['eded'],en=ens['eded'] ,a='TBlR'   ))  #
 ,('edcb',d(tp='cbr',tid='ed_s' ,l=  78 ,r=-270 ,p='ptop'   ,items=its['edcb']      ,vis=vis['edcb']                ,a='TBlR'   ))  #
 ,('edrf',d(tp='ch' ,tid='ed_s' ,l=  78 ,w=  60 ,p='ptop'   ,cap=_('f&alse')        ,vis=vis['edrf']                ,a='TB'     ))  # &a
 ,('edrt',d(tp='ch' ,tid='ed_s' ,l= 140 ,w=  60 ,p='ptop'   ,cap=_('t&rue')         ,vis=vis['edrt']                ,a='TB'     ))  # &r
 ,('brow',d(tp='bt' ,tid='ed_s' ,l=-270 ,w=  90 ,p='ptop'   ,cap=_('&...')          ,vis=vis['brow']                ,a='TBLR'   ))  # &.
 ,('toop',d(tp='bt' ,tid='ed_s' ,l=-270 ,w=  90 ,p='ptop'   ,cap=_('&GoTo')         ,vis=vis['toop'],hint=M.TOOP_H  ,a='TBLR'   ))  # &g
    # View def-value                                                                                                            
 ,('dfv_',d(tp='lb' ,tid='dfvl' ,l=   5 ,w=  70 ,p='ptop'   ,cap=_('>Defa&ult:')    ,hint=m.cur_op                  ,a='TB'     ))  # &u
 ,('dfvl',d(tp='ed' ,t=235      ,l=  78 ,r=-270 ,p='ptop'   ,ro_mono_brd='1,0,1'    ,sto=False                      ,a='TBlR'   ))  #
 ,('setd',d(tp='bt' ,tid='dfvl' ,l=-270 ,w=  90 ,p='ptop'   ,cap=_('Rese&t')                        ,en=ens['setd'] ,a='TBLR'   ))  # &t
    # For lexer/file                                                                                                            
#,('to__',d(tp='lb' ,tid='ed_s' ,l=-170 ,w=  30 ,p='ptop'   ,cap=_('>For:')                                         ,a='TBLR'   ))  # 
 ,('to__',d(tp='lb' ,tid='ed_s' ,l=-165 ,w=  30 ,p='ptop'   ,cap=_('For:')                                          ,a='TBLR'   ))  # 
 ,('tolx',d(tp='ch' ,tid='ed_s' ,l=-140 ,w=  70 ,p='ptop'   ,cap=_('Le&xer')                                        ,a='TBLR'   ))  # &x
 ,('tofi',d(tp='ch' ,tid='ed_s' ,l=- 85 ,w=  70 ,p='ptop'   ,cap=_('F&ile')         ,hint=tofi_c    ,en=tofi_en     ,a='TBLR'   ))  # &i
 ,('lexr',d(tp='cbr',tid='dfvl' ,l=-165 ,w= 160 ,p='ptop'   ,items=m.lexr_w_l                                       ,a='TBLR'   ))
    # Comment                                                                                                               
 ,('cmsp',d(tp='sp' ,y=cmnt_t-5                         ,ali=ALI_BT,sp_lr=5                                                     ))
 ,('cmnt',d(tp='me' ,t=cmnt_t   ,h=    m.h_cmnt                                                                                 
                                ,h_min=M.CMNT_MHT       ,ali=ALI_BT,sp_lrb=5       ,ro_mono_brd='1,1,1'                         ))
 ,('stbr',d(tp='sb' ,y=-M.STBR_H                                                                                                
                    ,h= M.STBR_H                        ,ali=ALI_BT                                                             ))
                ][1:]
        cnts    = odict(cnts)
        for cnt in cnts.values():
            if 'l' in cnt:  cnt['l']    = m.dlg_w+cnt['l'] if cnt['l']<0 else cnt['l']
            if 'r' in cnt:  cnt['r']    = m.dlg_w+cnt['r'] if cnt['r']<0 else cnt['r']
            if 'y' in cnt:  cnt['y']    = m.dlg_h+cnt['y'] if cnt['y']<0 else cnt['y']
        
        cnts['menu']['call']            = m.do_menu
        cnts['chps']['call']            = m.do_menu
        cnts['cpnm']['call']            = m.do_menu
        cnts['erpt']['call']            = m.do_menu
        cnts['apnw']['call']            = m.do_menu
        cnts['flt-']['call']            = m.do_fltr
        cnts['fltr']['call']            = m.do_fltr
        if m.live_fltr:
            cnts['cond']['call']        = m.do_fltr
        cnts['lexr']['call']            = m.do_lxfi
        cnts['tolx']['call']            = m.do_lxfi
        cnts['tofi']['call']            = m.do_lxfi
        cnts['lvls']['call']            = m.do_sele
        cnts['lvls']['on_click_header'] = m.do_sort
        cnts['srt0']['call']            = m.do_sort
        cnts['srt1']['call']            = m.do_sort
        cnts['srt2']['call']            = m.do_sort
        cnts['srt3']['call']            = m.do_sort
        cnts['srt4']['call']            = m.do_sort
        cnts['srt5']['call']            = m.do_sort
        cnts['srt6']['call']            = m.do_sort
        cnts['cmsp']['call']            = m.do_cust
        cnts['cws-']['call']            = m.do_cust
        cnts['lvls']['on_click_dbl']    = m.do_dbcl   #lambda idd,idc,data:print('on dbl d=', data)
        cnts['setd']['call']            = m.do_setv
        cnts['edcb']['call']            = m.do_setv
        cnts['edrf']['call']            = m.do_setv
        cnts['edrt']['call']            = m.do_setv
        cnts['brow']['call']            = m.do_setv
        cnts['toop']['call']            = m.do_setv
        cnts['help']['call']            = m.do_help
        return cnts
       #def get_cnts
    
    def get_vals(self, what=''):
        M,m = OptEdD,self
        m.cur_in    = m._prep_opt('key2ind')
        if not what or 'cur' in what:
            vis,ens,vas,its = m._prep_opt()
        if not what:
            # all
            return dict(cond=m.cond_s
                       ,lvls=m.cur_in
                       ,eded=vas['eded']
                       ,edcb=vas['edcb']
                       ,edrf=vas['edrf']
                       ,edrt=vas['edrt']
                       ,dfvl=vas['dfvl']
                       ,cmnt=vas['cmnt']
                       ,tolx=m.for_ulf=='l'
                       ,tofi=m.for_ulf=='f'
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
            if '+inlxfi' in what:
                rsp.update(dict(
                        tolx=m.for_ulf=='l'
                       ,tofi=m.for_ulf=='f'
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
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
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
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
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

        elif aid=='vali':
            if dlg_valign_consts():
                return d(ctrls=m.get_cnts())
            return []

        elif aid=='rslt':
            # Restore dlg/ctrls sizes
            fpr         = ag.fattrs()
            layout      = data
            m.col_ws    = layout.get('col_ws', m.col_ws)
            cmnt_h      = layout.get('cmnt_h', ag.cattr('cmnt', 'h'))
            dlg_h       = layout.get('dlg_h' , fpr['h'])
            dlg_w       = layout.get('dlg_w' , fpr['w'])
            return  d(ctrls=
                         m.get_cnts('+cols')+
                        [('cmnt', d(h=cmnt_h))
                        ,('stbr', d(y=dlg_h))   # Hack to push it at bottom (by Alex)
                    ],form=d(
                         h=dlg_h
                        ,w=dlg_w
                    ))
        elif aid=='svlt':
            # Save dlg/ctrls sizes
            m.col_ws        = [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
            layout          = data
            fpr             = ag.fattrs()
            layout['dlg_w'] = fpr['w']
            layout['dlg_h'] = fpr['h']
            layout['cmnt_h']= ag.cattr('cmnt', 'h')
            layout['col_ws']= m.col_ws
       #def do_cust
    
    def do_menu(self, aid, ag, data=''):
        pass;                  #LOG and log('aid={}',(aid))
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')

        scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
        if scam=='c' and aid=='menu':
            return m.do_cust('vali', ag)

        def wnen_menu(ag, tag):
            pass;              #LOG and log('tag={}',(tag))
            if False:pass
            
            elif tag[:3]=='ch:':
                return m.do_fltr('chps', ag, tag[3:])

            elif tag=='srt-':
                return m.do_sort('', ag, -1)
            elif tag[:3]=='srt':
                return m.do_sort('', ag, int(tag[3]))
            
            elif tag=='cws-':
                return m.do_cust(tag, ag)
            elif tag=='vali':
                return m.do_cust(tag, ag)
            
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
            
        #   elif tag=='dfns':
        #       m.col_ws    = [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
        #       new_file    = app.dlg_file(True, m.defn_path.name, str(m.defn_path.parent), 'JSONs|*.json')
        #       if not new_file or not os.path.isfile(new_file):    return []
        #       return m.do_file('set-dfns', new_file)
            elif tag=='full':
                m.col_ws    = [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]
                m.all_ops   = not m.all_ops
                m.opts_full = load_vals(m.opts_defn, 'lexer '+m.lexr+'.json', m.ed, m.all_ops)
                m.cur_op    = m.cur_op if m.cur_op in m.opts_full else ''
                m.do_file('build-chp-tree')
                m.stbr_act(M.STBR_ALL, len(m.opts_full))
                return d(ctrls=odict(m.get_cnts('+lvls +cur')))
            
            if tag=='apex':
                m.apply_one = not m.apply_one
                m.stores[m.subset+'apply_one']  = m.apply_one
            if tag=='apnw':
                ed.cmd(cmds.cmd_OpsReloadAndApply)
            if tag=='aufi':
                m.auto4file = not m.auto4file
                m.stores[m.subset+'auto4file']  = m.auto4file
        
            if tag=='lifl':
                m.live_fltr = not m.live_fltr
                m.stores[m.subset+'live_fltr']  = m.live_fltr
                m.cond_hl   = [s for s in m.stores.get(m.subset+'h.cond', []) if s] if not m.live_fltr else []
                return d(ctrls=m.get_cnts()
                        ,form =d(fid='cond')
                        )
        
            elif tag=='cpnm':
                app.app_proc(app.PROC_SET_CLIP, m.cur_op)
            elif tag=='erpt':
                body    = '\n'.join(m.chng_rpt)
#               app.msg_box('\n'.join(m.chng_rpt), app.MB_OK)
                dlg_wrapper(_('Сhanging steps')       ,500+10     ,400+10, 
                    [ dict(cid='body',tp='me' ,l=5,w=500  ,t=5,h=400, ro_mono_brd='1,0,0')]
                    , dict(body=body), focus_cid='body')
            elif tag=='locv':
        #       m.do_file('locate-opt')                     # while wait core fix
                if m.do_file('goto-opt'):   return None     #   need close dlg
            elif tag=='locd':
        #       m.do_file('locate-def')                     # while wait core fix
                if m.do_file('goto-def'):   return None     #   need close dlg

            elif tag[:4] in ('rslt', 'rmlt', 'svlt'):
                layouts_l   = m.stores.get(m.subset+'layouts', [])  # [{nm:Nm, dlg_h:H, dlg_w:W, ...}]
                layouts_d   = {lt['nm']:lt for lt in layouts_l}
                lt_i        = int(tag[4:])      if tag[:4] in ('rslt', 'rmlt')  else -1
                layout      = layouts_l[lt_i]   if lt_i>=0                      else None
                if 0:pass
                elif tag[:4]=='rmlt':
                    if  app.ID_OK != app.msg_box(
                                f(_('Remove layout "{}"?'), layout['nm'])
                                , app.MB_OKCANCEL+app.MB_ICONQUESTION): return []
                    del layouts_l[lt_i]
                elif tag=='svlt':
                    nm_tmpl     = _('#{}')
                    layout_nm   = f(nm_tmpl
                                   ,first_true(itertools.count(1+len(layouts_d))
                                            ,pred=lambda n:f(nm_tmpl, n) not in layouts_d))     # First free #N after len()
                    while True:
                        pass;  #LOG and log('layout_nm={!r}',(layout_nm))
                        layout_nm   = app.dlg_input('Name to save current sizes of the dialog and controls', layout_nm)
                        if not layout_nm:   return []
                        layout_nm   = layout_nm.strip()
                        if not layout_nm:   return []
                        if layout_nm in layouts_d and \
                            app.ID_OK != app.msg_box(
                                    f(_('Name "{}" already used. Overwrite?'), layout_nm)
                                    , app.MB_OKCANCEL+app.MB_ICONQUESTION): continue
                        break
                    layout      = None
                    if layout_nm in layouts_d:
                        layout  = layouts_d[layout_nm]  # Overwrite
                    else:
                        layout  = d(nm=layout_nm)       # Create
                        layouts_l+=[layout]
                    # Fill
                    m.do_cust(       'svlt', ag, layout)
                elif tag[:4]=='rslt':
                    return m.do_cust('rslt', ag, layout)
                # Save
                m.stores[m.subset+'layouts']    = layouts_l
                return []
            
            elif tag=='rprt':
                m.do_file('out-rprt')
            elif tag=='help':
                return m.do_help('', ag)
            return []
           #def wnen_menu
        pass;                  #LOG and log('',())

        if aid=='chps':
            def tree2menu(node, chp=''):
                mn_l    = [    d( tag='ch:'+                node['path']
                                , cap=f('{} ({})', chp, len(node['ops'])) 
                                , cmd=wnen_menu)
                              ,d( cap='-')
                          ] if chp else []
                for chp,kid in                              node['kids'].items():
                    mn_l   +=([d( cap=f('{} ({})', chp, len(kid['ops']))               
                                , sub=tree2menu(kid, chp))
                              ]
                                if 'kids' in kid else
                              [d( tag='ch:'+                kid['path']
                                , cap=f('{} ({})', chp, len(kid['ops']))               
                                , cmd=wnen_menu)
                              ]
                             )  
                return mn_l
               #def tree2menu
            mn_its  = tree2menu(m.chp_tree)
            ag.show_menu('chps', mn_its)

        if aid=='apnw': return wnen_menu(ag, aid)
        if aid=='cpnm': return wnen_menu(ag, aid)
        if aid=='erpt': return wnen_menu(ag, aid)
        
        if aid=='menu':
            locv_c  = f(M.LOCV_C, m.cur_op)
            locd_c  = f(M.LOCD_C, m.cur_op)
            lts_l   = m.stores.get(m.subset+'layouts', [])  # [{nm:Nm, dlg_h:H, dlg_w:W, ...}]
            full_en = not m.how.get('only_with_def', False) # Forbid to switch fo User+Lexer ops
            pass;              #lts_l   = [d(nm='Nm1'), d(nm='Nm2')]
            mn_its  = \
    [ d(    tag='full'          ,cap=_('&All options from User/Lexer')      ,ch=m.all_ops   ,en=full_en
    ),d(                         cap='-'
    ),d(                         cap=_('&Layout')           ,sub=
        [ d(tag='svlt'              ,cap=_('&Save current layout...')
        ),d(                         cap='-'
        )]+     (
        [ d(tag='rslt'+str(nlt)     ,cap=f(_('Restore layout "{}"'), lt['nm']))         for nlt, lt in enumerate(lts_l)
        ]+
        [ d(                         cap=_('&Forget layout'),sub=
            [ d(tag='rmlt'+str(nlt)     ,cap=f(_('Forget layout "{}"...'), lt['nm']))   for nlt, lt in enumerate(lts_l)
            ])
        ]       if lts_l else []) +
        [ d(                         cap='-'
        ),d(tag='vali'              ,cap=_('Adjust vertical alignments...')
        ),d(tag='cws-'              ,cap=_('Set default columns &widths')                       ,key='Alt+W'
        )]
    ),d(                         cap=_('&Table')            ,sub=
        [ d(tag='srt'+str(cn)       ,cap=f(_('Sort by column "{}"'), cs)    ,ch=m.sort[0]==cn   ,key='Alt+'+str(1+cn))
                                                            for cn, cs in enumerate(M.COL_NMS)
        ]+
        [ d(                         cap='-'
        ),d(tag='srt-'              ,cap=_('Clear sorting')                 ,en=(m.sort[0]!=-1)
        )]
    ),d(                         cap=_('More..&.')          ,sub=
        [ d(tag='locv'              ,cap=locv_c                             ,en=bool(m.cur_op)
        ),d(tag='locd'              ,cap=locd_c                             ,en=bool(m.cur_op)
        ),d(                         cap='-'
        ),d(tag='erpt'              ,cap=_('Show rep&ort of changes...')                        ,key='Alt+O'
        ),d(tag='apex'              ,cap=_('Apply changes on exit')         ,ch=m.apply_one
        ),d(tag='apnw'              ,cap=_('Appl&y changes now')            ,en=m.apply_need    ,key='Alt+Y'
        ),d(tag='aufi'              ,cap=_('Auto-update FILE options')      ,ch=m.auto4file
        ),d(                         cap='-'
        ),d(tag='lifl'              ,cap=_('Directly filter (w/o Enter, no History)')
                                                                            ,ch=m.live_fltr
        ),d(                         cap='-'
        ),d(tag='cpnm'              ,cap=_('&Copy option name')                                 ,key='Alt+C'
        )]
    ),d(                         cap='-'
    ),d(    tag='rprt'          ,cap=_('Create HTML &report')
    ),d(                         cap='-'
    ),d(    tag='help'          ,cap=_('&Help...')                                              ,key='Alt+H'
    )]
            pass;              #LOG and log('mn_its=¶{}',pf(mn_its))
            def add_cmd(its):
                for it in its:
                    if 'sub' in it: add_cmd(it['sub'])
                    else:                   it['cmd']=wnen_menu
            add_cmd(mn_its)
            ag.show_menu(aid, mn_its)
        return []
       #def do_menu

    def do_fltr(self, aid, ag, data=''):
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]

        fid     = ag.fattr('fid')
        pass;                  #LOG and log('aid,fid={}',(aid,fid))
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
            fid         = '' if m.live_fltr else 'lvls'
#           fid         = 'lvls'
        if aid=='fltr':
            m.cond_s    = ag.cval('cond')
            m.cond_hl   = add_to_history(m.cond_s, m.cond_hl)       if m.cond_s and not m.live_fltr else m.cond_hl
            fid         = 'lvls'
        if aid=='flt-':
            m.cond_s    = ''
            fid         = 'cond'

        if aid=='chps':
            # Append selected chapter as filter value
            path        = '@'+data
            if path not in m.cond_s:
                m.cond_s    = re.sub(r'@([\w/]*)', '', m.cond_s).strip()    # del old 
                m.cond_s    = (m.cond_s+' '+path).strip()                   # add new
                m.cond_hl   = add_to_history(m.cond_s, m.cond_hl)   if not m.live_fltr else m.cond_hl
            fid         = 'cond'

        # Select old/new op
        m.cur_op= m._prep_opt('ind2key')
        ctrls   = m.get_cnts('+lvls')
        m.cur_in= m._prep_opt('key2ind')
        if m.cur_in<0 and m.SKWULFs:
            # Sel top if old hidden
            m.cur_in= 0
            m.cur_op= m._prep_opt('ind2key', ind=m.cur_in)
        return d(ctrls=m.get_cnts('+cond =lvls +cur')
                ,vals =m.get_vals()
                ,form =d(fid=fid)
                )
               
       #def do_fltr
    
    def do_sort(self, aid, ag, col=-1):
        pass;                  #LOG and log('col={}',(col))
        pass;                  #return []
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
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
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
        pass;                  #LOG and log('data,m.cur_op,m.cur_in={}',(data,m.cur_op,m.cur_in))
        m.cur_op= m._prep_opt('ind2key')
        pass;                  #LOG and log('m.cur_op,m.cur_in={}',(m.cur_op,m.cur_in))
        return d(ctrls=odict(m.get_cnts('+cur'))
                ,vals =      m.get_vals('cur')
                )
       #def do_sele
    
    def do_lxfi(self, aid, ag, data=''):
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
        pass;                  #LOG and log('aid={}',(aid))
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]

        if False:pass
        elif aid in ('tolx', 'tofi'):
            # Changed "For Lexer/File"
            m.for_ulf   = 'l' if aid=='tolx' and ag.cval('tolx') else \
                          'f' if aid=='tofi' and ag.cval('tofi') else \
                          'u'
            fid         = 'lexr' \
                            if m.for_ulf=='l' and m.lexr not in m.lexr_l else \
                          m._prep_opt('fid4ed')
            return d(ctrls=m.get_cnts('+cur')
                    ,vals =m.get_vals('+cur+inlxfi')
                    ,form =d(fid=fid)
                    )
        elif aid=='lexr':
            # Change current lexer
            lexr_n  = ag.cval('lexr')
            m.lexr  = m.lexr_l[lexr_n]      if lexr_n>=0 else ''
            m.cur_op= m._prep_opt('ind2key')
            m.do_file('load-data')
            ctrls   = m.get_cnts('+lvls')
            m.cur_in= m._prep_opt('key2ind')
            if m.cur_in<0 and m.SKWULFs:
                # Sel top if old hidden
                m.cur_in= 0
                m.cur_op= m._prep_opt('ind2key', ind=m.cur_in)
            elif m.cur_in<0:
                m.cur_op= ''
            return d(ctrls=m.get_cnts('=lvls +cur')
                    ,vals =m.get_vals()#'+lvls +cur')
                    )
       #def do_lxfi
    
    def do_dbcl(self, aid, ag, data=''):
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
        pass;                  #LOG and log('data,m.cur_op,m.cur_in={}',(data,m.cur_op,m.cur_in))
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
        pass;                  #LOG and log('op_r,op_c,m.cur_op,m.cur_in={}',(op_r,op_c,m.cur_op,m.cur_in))
        pass;                  #LOG and log('op_r,op_c={}',(op_r,op_c))
        if False:pass
        elif op_c not in (M.COL_DEF,M.COL_USR,M.COL_LXR,M.COL_FIL):
            return []
        elif -1==op_r:
            pass;              #LOG and log('skip as no opt',())
            return []
        elif -1==op_c:
            pass;              #LOG and log('skip as miss col',())
            return []
        elif M.COL_DEF==op_c:
            return d(form =d(fid='setd'))
        elif M.COL_USR==op_c and m.for_ulf!='u':
            # Switch to user vals
            m.for_ulf   = 'u'
        elif M.COL_LXR==op_c and m.for_ulf!='l':
            # Switch to lexer vals
            m.for_ulf   = 'l'
        elif M.COL_FIL==op_c and m.for_ulf!='f':
            # Switch to lexer vals
            m.for_ulf   = 'f'
        else:
            return []
        pass;                   LOG and log('op_r,op_c,m.for_ulf={}',(op_r,op_c,m.for_ulf))
        return d(ctrls=m.get_cnts('+cur')
                ,vals =m.get_vals('+cur+inlxfi')
                ,form =d(fid=m._prep_opt('fid4ed'))
                )
       #def do_dbcl
    
    def do_setv(self, aid, ag, data=''):
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
        pass;                  #LOG and log('aid,m.cur_op={}',(aid,m.cur_op))
        if not m.cur_op:   return []
        m.col_ws= [ci['wd'] for ci in m.ag.cattr('lvls', 'cols')]

        if aid=='toop':
#           m.do_file('locate-opt')                     # while wait core fix
            if m.do_file('goto-opt'):   return None     #   need close dlg
            return []
        
        trg     = 'lexer '+m.lexr+'.json' if m.for_ulf=='l' else 'user.join'
        key4v   = m.for_ulf+'val'
        op      = m.cur_op
        oi      = m.opts_full[op]
        frm     = oi['frm']
#       if frm=='json':
#           m.stbr_act(M.STBR_MSG, f(_('Edit {!r} to change value'), trg))
#           return []
        dval    = oi.get( 'def')
        uval    = oi.get('uval')
        lval    = oi.get('lval')
        fval    = oi.get('fval')
        ulfvl   = oi.get(key4v ) #fval if m.for_ulf=='f' else lval if m.for_ulf=='l' else uval
        jval    = oi['jlvl']    if m.for_ulf=='l' else \
                  oi['juvl']    if m.for_ulf=='u' else \
                  oi['jfvl']
        scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
        
        # Get new value
        newv    = None
        erpt_s  = ''
        if False:pass
        
        elif aid=='setd'        and \
             m.for_ulf=='f'     and \
             op in apx.OPT2PROP:
            # Remove from file - set over def/user/lex val
            newv    = oi.get('lval', oi.get('uval', oi.get('def')))
            if newv==ulfvl:
                m.stbr_act(M.STBR_MSG, _('No need changes'))
                return []
            erpt_s  = 'reset-f'
            m.ed.set_prop(apx.OPT2PROP[op], newv)
            
        elif aid=='setd'        and \
             ulfvl is not None  and \
             m.for_ulf!='f':
            # Remove from user/lexer
            if  scam!='c' and \
                app.ID_OK != app.msg_box(f(_('Remove {} option'
                                            '\n   {} = {!r}'
                                            '\n?'), 'LEXER' if m.for_ulf=='l' else 'USER', op, jval)
                                        , app.MB_OKCANCEL+app.MB_ICONQUESTION): return []
            newv= None
        
        elif aid=='brow' and frm in ('hotk', 'file'):
            m.stbr_act(M.STBR_MSG, f(_('Default value: "{}". Old value: "{}"'), dval, ulfvl))
            newv    = (app.dlg_hotkey(op)                                       if frm=='hotk' else
                       app.dlg_file(True, '', os.path.expanduser(ulfvl), '')    if frm=='hotk' else None)
            m.stbr_act(M.STBR_MSG, '')
            if not newv:    return []
        
        elif aid=='setv':                   # Add/Set opt for user/lexer/file
            # Enter from edit. Need parse some string
            newv    = m.ag.cval('eded')
            try:
                newv    =   int(newv)   if frm=='int'   else \
                          float(newv)   if frm=='float' else \
                                newv
            except Exception as ex:
                app.msg_box(f(_('Incorrect value. It\'s needed in format: {}'), frm)
                           , app.MB_OK+app.MB_ICONWARNING)
                return d(form=d(fid='eded'))
        elif aid in ('edrf', 'edrt'):       # Add/Set opt for user/lexer/file
            newv    = aid=='edrt'
            newv    = not newv if newv==ulfvl else newv
        elif aid=='edcb':                   # Add/Set opt into user/lexer/file
            pass;              #LOG and log('oi={}',(oi))
            vl_l    = [k for k,v in oi.get('dct', [])]  if 'dct' in oi else oi.get('lst', [])
            pass;              #LOG and log('vl_l={}',(vl_l))
            pass;              #LOG and log('m.ag.cval(edcb)={}',(m.ag.cval('edcb')))
            newv    = vl_l[m.ag.cval('edcb')]
            pass;              #LOG and log('newv={}',(newv))

        # Use new value to change env
        if newv is not None and newv==ulfvl:
            m.stbr_act(M.STBR_MSG, _('No need changes'))
            return []
        
        if m.for_ulf=='f' and newv is not None and op in apx.OPT2PROP:
            # Change for file
            erpt_s  = 'set-f'
            ed.set_prop(apx.OPT2PROP[op], newv)
            
        if m.for_ulf!='f':
            # Change target file
            pass;              #LOG and log('?? do_erpt',())
            erpt_s  =('reset-u' if newv  is None and m.for_ulf=='u' else
                      'reset-l' if newv  is None and m.for_ulf=='l' else
                      'add-u'   if ulfvl is None and m.for_ulf=='u' else
                      'add-l'   if ulfvl is None and m.for_ulf=='l' else
                      'set-u'   if                   m.for_ulf=='u' else
                      'set-l'   if                   m.for_ulf=='l' else '')
            pass;              #LOG and log('?? set_opt',())
            apx.set_opt(op
                       ,newv
                       ,apx.CONFIG_LEV_LEX if m.for_ulf=='l' else apx.CONFIG_LEV_USER
                       ,ed_cfg  =None
                       ,lexer   =m.lexr
                       )

            if not m.apply_one:
                pass;          #LOG and log('?? OpsReloadAndApply',())
                ed.cmd(cmds.cmd_OpsReloadAndApply)
            else:
                m.apply_need    = True
            
        # Use new value to change dlg data
        pass;                  #LOG and log('?? oi={}',(oi))
#       pass;                   LOG and log('?? m.opts_full={}',pf(m.opts_full))
        if False:pass
        elif aid=='setd':
            oi.pop(key4v, None)     if m.for_ulf!='f' else 0
        else:
            pass;              #LOG and log('key4v, newv={}',(key4v, newv))
            oi[key4v] = newv
        pass;                  #LOG and log('oi={}',(oi))
        upd_cald_vals(m.opts_full)
        pass;                  #LOG and log('oi={}',(oi))
        
        jnewv   = oi['jlvl']   if m.for_ulf=='l' else oi['juvl']    if m.for_ulf=='u' else oi['jfvl']
        m.do_erpt(erpt_s, jnewv, jval)
        pass;                  #LOG and log('ok oi={}',(oi))
#       pass;                   LOG and log('ok m.opts_full={}',pf(m.opts_full))
        
        pass;                  #LOG and log('?? get_cnts',())
        
        if m.for_ulf!='f' and m.auto4file and op in apx.OPT2PROP:
            # Change FILE to over
            newv    = oi.get('lval', oi.get('uval', oi.get('def')))
            if newv!=oi.get('fval'):
                erpt_s      = 'reset-f'
                m.ed.set_prop(apx.OPT2PROP[op], newv)
                oi['fval']  = newv
                jval        = oi['jfvl']
                upd_cald_vals(m.opts_full)
                jnewv       = oi['jfvl']
                m.do_erpt('auset-f', jnewv, jval)
        
        pass;                  #LOG and log('m.get_vals(lvls-cur)={}',(m.get_vals('lvls-cur')))
        return d(ctrls=m.get_cnts('+lvls+cur')
                ,vals =m.get_vals('lvls-cur')
                )
       #def do_setv

    def do_erpt(self, what='', jnewv=None, joldv=None):
        pass;                  #LOG and log('what, newv={}',(what, newv))
        M,m = OptEdD,self
        
        if 0==len(m.chng_rpt):
            rpt = f('Starting to change options at {:%Y-%m-%d %H:%M:%S}', datetime.datetime.now())
#           print(rpt)
            m.chng_rpt += [rpt]
        
        oi  = m.opts_full[m.cur_op]
        oldv= None
        if 0:pass
        elif what=='reset-f':
            rpt     = f(_('Set FILE option to overridden value {!r}')       ,jnewv)
        elif what=='set-f':
            rpt     = f(_('Set FILE option to {!r}')                        ,jnewv)
        elif what=='auset-f':
            rpt     = f(_('Auto-set FILE option to overridden value {!r}')  ,jnewv)
        elif what=='reset-l':
            rpt     = f(_('Remove LEXER {!r} option')               ,m.lexr       )
        elif what=='set-l':
            rpt     = f(_('Set LEXER {!r} option to {!r}')          ,m.lexr ,jnewv)
        elif what=='add-l':
            rpt     = f(_('Add LEXER {!r} option {!r}')             ,m.lexr ,jnewv)
        elif what=='reset-u':
            rpt     = f(_('Remove USER option')                                   )
        elif what=='set-u':
            rpt     = f(_('Set USER option to {!r}')                        ,jnewv)
        elif what=='add-u':
            rpt     = f(_('Add USER option {!r}')                           ,jnewv)
        else:
            return 
        rpt         = f('{} (from {!r})', rpt, joldv) \
                        if what[:3]!='add' and joldv is not None else rpt
        rpt         = rpt.replace('True', 'true').replace('False', 'false')
        rpt         = m.cur_op + ': '               + rpt
        rpt         = f('{}. ', len(m.chng_rpt))  + rpt
#       print(rpt)
        m.stbr_act(M.STBR_MSG, rpt + _('   [Alt+O - all changes]'))
        m.chng_rpt += [rpt]
       #def do_erpt
    
    def do_help(self, aid, ag, data=''):
        M,m = OptEdD,self
        m.stbr_act(M.STBR_MSG, '')
        pass;                  #LOG and log('',())
        dlg_wrapper('Help'
        ,   510, 510 
        ,   [d(cid='body', tp='me', l=5, t=5, w=500, h=500, ro_mono_brd='1,1,0')]
        ,   d(      body=   #NOTE: help
                 f(
  _(  'About "{fltr}"'
    '\r '
   )
   +M.FLTR_H+
  _('\r '
    '\rOther tips.'
    '\r • Use ENTER to filter table and to change or reset value.'
    '\r • Use double click on any cell in columns'
    '\r     "{c_usr}"'
    '\r     "{c_lxr}"'
    '\r     "{c_fil}"'
    '\r   to change "{in_lxr}" flag and to put focus on the value field.'
    '\r • Use double click on any cell in column'
    '\r     "{c_def}"'
    '\r   to put focus on "{reset}".'
    '\r • Click on "{reset}" will ask to confirm for User and Lexer options.'
    '\r   Hold Ctrl to skip confirmation.'
    '\r • If currrent options is not visible see its name in tooltip'
    '\r   when cursor over label User/Lexer/File'
    '\r • See name of file (or name of tag) in tooltip'
    '\r   when cursor over checkbutton File'
   )             , c_usr=M.COL_NMS[M.COL_USR]
                 , c_lxr=M.COL_NMS[M.COL_LXR]
                 , c_fil=M.COL_NMS[M.COL_FIL]
                 , c_def=M.COL_NMS[M.COL_DEF]
                 , fltr = ag.cattr('flt_', 'cap', live=False).replace('&', '').strip(':')
                 , in_lxr=ag.cattr('tolx', 'cap', live=False).replace('&', '')
                 , reset= ag.cattr('setd', 'cap', live=False).replace('&', '')
                 ))
        )
        return []
       #def do_help
    
   #class OptEdD


class Command:
    def dlg_cuda_options(self):
        if app.app_api_version()<MIN_API_VER:   return app.msg_status(_('Need update CudaText'))
        pass;                  #LOG and log('ok',())
        pass;                  #dlg_opt_editor('CudaText options', '')
        pass;                  #return 
        OptEdD(
                                #path_keys_info=r'c:\Programs\CudaText\py\cuda_find_in_files\fif_opts_def.json'
                               #,subset='fif-df.'
                                #path_keys_info=apx.get_def_setting_dir()          +os.sep+'kv-default.json'   #NOTE: srcs
          path_keys_info=apx.get_def_setting_dir()          +os.sep+'default.json'
        , subset='df.'
        ).show(_('CudaText options'))
       #def dlg_cuda_options

    def dlg_cuda_opts_deprecated(self):
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
       #def dlg_cuda_opts_deprecated
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
            return app.msg_status(_('No source for key-info'))
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
                return app.msg_status(_('Bad source for key-info'))
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

        pass;                  #LOG and log('cnts={}',(cnts))
        aid, vals, fid, chds = dlg_wrapper(f('{} ({})', title, VERSION_V), DLG_W, DLG_H, cnts, vals, focus_cid=fid)
        if aid is None or aid=='-':  return

        if aid=='-flt':
            vals['cond']    = ''
        if aid=='-cha':
            vals['chap']    = 0
        if aid=='fltr' and fid=='eded':     # Подмена умолчательной кнопки по активному редактору
            aid = 'setv'

        pass;                  #LOG and log('aid={}',(aid))

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

def add_to_history(val:str, lst:list, max_len=MAX_HIST, unicase=False)->list:
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
                dirs    = [d for d in os.listdir(from_dir) if os.path.isdir(from_dir+os.sep+d) and d.strip()]
                dirs    = sorted(dirs)
                dctF    = odict([(d,d) for d in dirs])
#               dctF    = {d:d for d in os.listdir(from_dir) if os.path.isdir(from_dir+os.sep+d)}
                pass;          #LOG and log('dctF={}',(dctF))
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
                   #log('Too few variants ({}) for key {}',len(dct), key) if len(dct)<2 else None
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
    word-break:     break-all;
}
td.win {
    font-weight:    bold;
    word-break:     break-all;
}
    </style>
</head>
<body>
'''
RPT_FOOT = '''
</body>
</html>
'''

def do_report(fn, lex='', ed_=ed):
    def hard_word_wrap(text, rmax):
        reShift     = re.compile(r'\s*')
        reHeadTail  = re.compile(r'(.{' + str(rmax) + r'}\S*)\s*(.*)')
        src_lines   = text.splitlines()
        pass;                  #print('src_lines=',src_lines)
        trg_lines   = []
        for line in src_lines:
            pass;              #print('line=', line, 'len=', len(line.rstrip()))
            if len(line.rstrip()) <= rmax: 
                trg_lines.append(line)
                continue
            shift   = reShift.match(line).group(0)
            head,   \
            tail    = reHeadTail.match(line).group(1, 2)
            if not tail:
                tail= line.split()[-1]
                head= line[:-len(tail)]
            pass;              #print('head=', head, 'tail=', tail)
            trg_lines.append(head)
            trg_lines.append(shift+tail)
        pass;                  #print('trg_lines=',trg_lines)
        return '\n'.join(trg_lines)
       #def hard_word_wrap
       
#   lex         = ed_.get_prop(app.PROP_LEXER_CARET)
    def_json    = apx.get_def_setting_dir()         +os.sep+'default.json'
    usr_json    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'user.json'
    lex_json    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+lex                                 if lex else ''

    def_opts    = apx._get_file_opts(def_json, {},  object_pairs_hook=collections.OrderedDict)
    usr_opts    = apx._get_file_opts(usr_json, {},  object_pairs_hook=collections.OrderedDict)
    lex_opts    = apx._get_file_opts(lex_json, {},  object_pairs_hook=collections.OrderedDict)  if lex else None

    def_opts    = pickle.loads(pickle.dumps(def_opts))                              # clone to pop
    usr_opts    = pickle.loads(pickle.dumps(usr_opts))                              # clone to pop
    lex_opts    = pickle.loads(pickle.dumps(lex_opts))  if lex else {}              # clone to pop

    fil_opts    = {op:ed_.get_prop(pr) for op,pr in apx.OPT2PROP.items()}
#   fil_opts    = get_ovrd_ed_opts(ed)
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
        f.write('<h4>High priority: editor options</h4>\n')
        f.write('<table>\n')
        f.write(    '<tr>\n')
        f.write(    '<th>Option name</th>\n')
        f.write(    '<th>Value in<br>default</th>\n')
        f.write(    '<th>Value in<br>user</th>\n')
        f.write(    '<th>Value in<br>{}</th>\n'.format(lex))                                                            if lex else None
        f.write(    '<th title="{}">Value for file<br>{}</th>\n'.format(ed_.get_filename()
                                              , os.path.basename(ed_.get_filename())))
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
#           f.write(    '<td><pre>{}</pre></td>\n'.format(cmt_opts.get(opt, '')))
            f.write(    '<td><pre>{}</pre></td>\n'.format(hard_word_wrap(cmt_opts.get(opt, ''), 50)))
            f.write(    '</tr>\n')
            def_opts.pop(opt, None)
            usr_opts.pop(opt, None)
            lex_opts.pop(opt, None)                                                                                     if lex else None
        f.write('</table><br/>\n')
        f.write('<h4>Overridden default options</h4>\n')
        f.write('<table>\n')
        f.write(    '<tr>\n')
        f.write(    '<th width="15%">Option name</th>\n')
        f.write(    '<th width="20%">Value in<br>default</th>\n')
        f.write(    '<th width="20%">Value in<br>user</th>\n')
        f.write(    '<th width="10%">Value in<br>{}<br></th>\n'.format(lex))                                            if lex else None
        f.write(    '<th width="35%">Comment</th>\n')
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
            f.write(    '<td><pre>{}</pre></td>\n'.format(hard_word_wrap(cmt_opts.get(opt, ''), 50)))
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

#def get_ovrd_ed_opts(ed):
#   ans     = collections.OrderedDict()
#   ans['tab_size']             = ed.get_prop(app.PROP_TAB_SIZE)
#   ans['tab_spaces']           = ed.get_prop(app.PROP_TAB_SPACES)
#   ans['wrap_mode']            = ed.get_prop(app.PROP_WRAP)
#   ans['unprinted_show']       = ed.get_prop(app.PROP_UNPRINTED_SHOW)
#   ans['unprinted_spaces']     = ed.get_prop(app.PROP_UNPRINTED_SPACES)
#   ans['unprinted_ends']       = ed.get_prop(app.PROP_UNPRINTED_ENDS)
#   ans['unprinted_end_details']= ed.get_prop(app.PROP_UNPRINTED_END_DETAILS)
#   return ans
#  #def get_ovrd_ed_opts(ed):

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
[+][at-kv][05apr17] Preview for format=fontmay
[+][kv-kv][06apr17] Spec filter sign: * - to show only modified
[-][kv-kv][06apr17] Format color
[+][kv-kv][24apr17] Sort as Def or as User
[+][kv-kv][05may17] New type "list of str"
[ ][kv-kv][23jun17] ? Filter with tag (part of tag?). "smth #my"
[+][kv-kv][15mar18] ? Filter with all text=key+comment
[+][kv-kv][19mar18] ? First "+" to filter with comment
[-][kv-kv][19mar18] !! Point the fact if value is overed in ed
[?][kv-kv][20mar18] Allow to add/remove opt in user/lex
[?][kv-kv][21mar18] ? Allow to meta keys in user.json: 
                        "_fif_LOG__comment":"Comment for fif_LOG"
[+][kv-kv][22mar18] Set conrol's tab_order to always work Alt+E for "Valu&e"
[ ][kv-kv][26mar18] Use editor for comment
[+][kv-kv][26mar18] Increase w for one col when user increases w of dlg (if no h-scroll)
[+][kv-kv][13apr18] DClick on Def-col - focus to Reset
[-][kv-kv][16apr18] Open in tag for fmt=json
[?][kv-kv][23apr18] ? Show opt from cur line if ed(default.json)
[+][at-kv][03may18] Rework ask to confirm removing user/lex opt
[+][at-kv][04may18] Report to console all changes
[+][at-kv][05may18] Call OpsReloadAndApply
[+][kv-kv][05may18] Rework radio to checks (Linux bug: always set one of radio-buttons)
[-][kv-kv][05may18] Ask "Set also for current file?" if ops is ed.prop
[+][kv-kv][06may18] Menu command "Show changes"
[+][kv-kv][06may18] Show all file opt value. !!! only if val!=over-val
[+][kv-kv][06may18] Rework Sort
[ ][kv-kv][14may18] Scale def col widths
[ ][at-kv][14may18] DClick over 1-2-3 is bad
[ ][at-kv][14may18] Allow to refresh table on each changong of filter 
'''