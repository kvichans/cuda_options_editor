''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.1.0 2017-04-05'
ToDo: (see end of file)
'''

import  re, os, sys, json, collections

import  cudatext            as app
import  cudax_lib           as apx
from    .cd_plug_lib    import *

OrdDict = collections.OrderedDict

pass;                           LOG     = (-1==-1)          # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)
pass;                           ##!! waits correction

_   = get_translation(__file__) # I18N

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')
#MIN_API_VER = '1.0.168'
MAX_HIST    = apx.get_opt('ui_max_history_edits', 20)
CFG_JSON    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_options_editor.json'


class Command:
    def dlg_cuda_opts(self):
        pass;                  #LOG and log('ok',())
        pass;                  #dlg_opt_editor('CudaText options', '')
        pass;                  #return 
#       cuda_opts   = apx.get_def_setting_dir()+os.sep+'default_options.json'
#       cuda_opts   = os.path.dirname(__file__)+os.sep+'default_options.json'
#       dlg_opt_editor('CudaText options', json.loads(open(cuda_opts).read()))
        dlg_opt_editor('CudaText options'
        , keys_info=None
#       , path_raw_keys_info=apx.get_def_setting_dir()          +os.sep+'kv-default_tmp.json'
        , path_raw_keys_info=apx.get_def_setting_dir()          +os.sep+'default.json'
#       , path_raw_keys_info=apx.get_def_setting_dir()          +os.sep+'kv-default.json'
        , path_svd_keys_info=app.app_path(app.APP_DIR_SETTINGS) +os.sep+'default_keys_info.json'
        )
       #def dlg_cuda_opts
   #class Command

def dlg_opt_editor(title, keys_info=None
        , path_to_json='settings/user.json'
        , path_raw_keys_info=''
        , path_svd_keys_info=''
        , subset='def.'
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
    if not keys_info:
        if not os.path.isfile(path_raw_keys_info):
            return app.msg_status(_('No sourse for key-info'))
        # If ready json exists - use ready
        # Else - parse raw (and save as ready)

        mtime_raw   = os.path.getmtime(path_raw_keys_info)
        mtime_svd   = os.path.getmtime(path_svd_keys_info) if os.path.exists(path_svd_keys_info) else 0
        if 'use ready'!='use ready' and mtime_raw < mtime_svd:
            # Use ready
            keys_info   = json.loads(open(path_svd_keys_info, encoding='utf8').read(), object_pairs_hook=OrdDict)
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
            
    if -1== 1:  # Test data
        keys_info = [dict(key='key-bool',format='bool'  ,def_val=False           ,comment= 'smth')
                    ,dict(key='key-int' ,format='int'   ,def_val=123             ,comment= 'smth\nsmth')
                    ,dict(key='key-aint'                ,def_val=123             ,comment= 'smth\nsmth')
                    ,dict(key='key-str' ,format='str'   ,def_val='xyz'           ,comment= 'smth')
                    ,dict(key='key-flo' ,format='float' ,def_val=1.23            ,comment= 'smth')
                    ,dict(key='key-aflo'                ,def_val=1.23            ,comment= 'smth')
                    ,dict(key='key-font',format='font'  ,def_val=''              ,comment= 'smth')
                    ,dict(key='key-file',format='file'  ,def_val=''              ,comment= 'smth')
                    ,dict(key='key-en_i',format='enum_i',def_val=1               ,comment= 'smth',   dct={0:'000', 1:'111', 2:'222'})
                    ,dict(key='key-en_s',format='enum_s',def_val='b'             ,comment= 'smth',   dct=[('a','AA'), ('b','BB'), ('c','CC')])
                    ,dict(key='key-json',format='json'  ,def_val={'x':{'a':1}}   ,comment= 'Style')
                    ]
        path_to_json=os.path.dirname(__file__)+os.sep+'test.json'

    if 0==len(keys_info):
        return app.msg_status(_('Empty keys_info'))

    font_l  = [] if app.app_api_version()<'1.0.174' else \
              [font 
                for font in app.app_proc(app.PROC_ENUM_FONTS, '')
                if not font.startswith('@')] 
    if 'cut fonts'!='cut fonts':
        font_l  = font_l[:2]
    pass;                   LOG#and log('font_l={}',(font_l))

    stores      = json.loads(open(CFG_JSON).read(), object_pairs_hook=OrdDict) \
                    if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                  OrdDict()

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
        or isinstance(kv, dict) or isinstance(kv, list):
            return json.loads(strv, object_pairs_hook=OrdDict)
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
    k2fdcvt = OrdDict([
            (       kinfo['key'],
               {'f':kinfo.get('format', frm_of_val(kinfo['def_val']))
               ,'t':kinfo.get('dct')            if ('dct' not in kinfo or   isinstance(kinfo.get('dct'), dict)) else 
                    OrdDict(kinfo.get('dct'))
               ,'d':kinfo['def_val']
               ,'c':kinfo['comment']            if                          isinstance(kinfo['comment'], str) else
                    '\n'.join(kinfo['comment'])
               ,'v':apx.get_opt(kinfo['key'], kinfo['def_val'])
               ,'a':kinfo.get('chapter', '')
               ,'g':set(kinfo.get('tags', []))
               }
            )  for  kinfo in keys_info
            ])
    pass;                      #LOG and log('k2fdcvt={}',(k2fdcvt))

    fltr_h  = _('Suitable keys will contain all specified words.'
              '\rTips:'
              '\r • Use "<" or ">" for word boundary.'
              '\r     size> <tab'
              '\r   selects "tab_size" but not "ui_tab_size" or "tab_size_x".')
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
    while True: #NOTE: json_props
        COL_WS      = [                 stores.get(subset+'cust.wd_k', 250)
                      ,                 stores.get(subset+'cust.wd_f',  50)
                      ,                 stores.get(subset+'cust.wd_s',  20)
                      ,                 stores.get(subset+'cust.wd_v', 250)]         # Widths of listview columns 
        CMNT_H      =                   stores.get(subset+'cust.ht_c',  55)          # Height of Comment memo
        LST_W, LST_H= sum(COL_WS)+20,   stores.get(subset+'cust.ht_t', 100)-5        # Listview sizes
        DLG_W, DLG_H= 5+LST_W+5+80+5 \
                    , 5+20+30+LST_H+5+30+5+30+5+CMNT_H+5     # Dialog sizes
        l_val   = DLG_W-10-80-20-COL_WS[-1]
        
        # Filter with 
        #   cond_s
        #   chap_n, chap_s
        #   tags_set
        chap_s  = chap_l[chap_n]
        pass;                  #LOG and log('chap_n,chap_s={}',(chap_n,chap_s))
        fl_kfsvt= [ (knm
                    ,fdcv['f']
                    ,'*' if fdcv['d']!=fdcv['v'] else ''
                    ,fdcv['v']
                    ,fdcv['t']
                    ,f('{}: ',fdcv['a'])                if chap_l and chap_n==0 and fdcv['a'] else ''
                    ,f(' (#{})',', #'.join(fdcv['g']))  if tags_l and               fdcv['g'] else ''
                    )
                    for (knm, fdcv) in k2fdcvt.items()
                    if  (cond_s==''     or test_cond(cond_s.upper(), knm))  and
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
                  font_l                                                         \
                                        if frm_sel=='font' and     font_l   else \
                  None
        sel_sel = index_1(list(dct_sel.keys()), val_sel) \
                                        if frm_sel in ('enum_i', 'enum_s')  else \
                  index_1(font_l,               val_sel)                         \
                                        if frm_sel=='font' and     font_l   else \
                  -1
        
        stat    = f(' ({}/{})', len(fl_kfsvt), len(k2fdcvt))
        col_aws = [p+cw for (p,cw) in zip(('', 'C', 'C', ''), map(str, COL_WS))]
        itms    = (zip([_('Key')+stat, _('Type'),   _(' '), _('Value')], col_aws)
                  ,    [ ( kch+knm+ktg,   kf,          kset,   to_str(kv, kf, kdct)) for
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
        as_char = key_sel and (frm_sel in ('int', 'float', 'str', 'json')   or frm_sel=='font' and not font_l)
        as_enum = key_sel and (frm_sel in ('enum_i', 'enum_s')              or frm_sel=='font' and     font_l)
        as_file = key_sel and  frm_sel in ('file')
        cnts    =([]
                # Filter
                 +[dict(cid='fltr',tp='bt'  ,t=0        ,l=0            ,w=0            ,cap=''                 ,def_bt='1'         )] # 
                 +[dict(           tp='lb'  ,t=5        ,l=5+2          ,w=COL_WS[0]    ,cap=_('&Filter:')  ,hint=fltr_h            )] # &k
                 +[dict(cid='cond',tp='cb'  ,t=25       ,l=5+2          ,w=COL_WS[0]    ,items=cond_hl                              )] #
            # Chapters
            +([] if 1==len(chap_l) else []
                 +[dict(           tp='lb'  ,t=5        ,l=15+COL_WS[0] ,w=140          ,cap=_('Se&ction:')                         )] # &c
                 +[dict(cid='chap',tp='cb-ro',t=25      ,l=15+COL_WS[0] ,w=140          ,items=chap_v                       ,act='1')] #
            )
            # Tags
            +([] if not tags_l else []
                 +[dict(           tp='lb'  ,t=5        ,l=COL_WS[0]+160,r=DLG_W-10-80  ,cap=_('T&ags:')                            )] # &a
                 +[dict(cid='tags',tp='cb-ro',t=25      ,l=COL_WS[0]+160,r=DLG_W-10-80  ,items=tags_hl                      ,act='1')] #
                 +[dict(cid='?tgs',tp='bt'  ,tid='tags' ,l=DLG_W-5-80   ,w=80           ,cap=_('Tag&s…')    ,hint=_('Choose tags')  )] # &s
                 +[dict(cid='-tgs',tp='bt'  ,t=57       ,l=DLG_W-5-80   ,w=80           ,cap=_('Clea&r')    ,hint=_('Clear tags')   )] # &r
            )
                # Table
                 +[dict(cid='lvls',tp='lvw' ,t=57       ,l=5 ,h=LST_H   ,w=LST_W        ,items=itms             ,grid='1'   ,act='1')] #
            # Editors for value
            +([] if not as_bool else []
                 +[dict(           tp='lb'  ,tid='kvbl' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kvbl',tp='ch'  ,t=65+LST_H ,l=l_val+5      ,w=COL_WS[-1]+15,cap=_('O&n')                       ,act='1')] # &n
            )
            +([] if not as_char else []
                 +[dict(           tp='lb'  ,tid='kved' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kved',tp='ed'  ,t=65+LST_H ,l=l_val+5      ,w=COL_WS[-1]+15                                            )] #
                 +[dict(cid='setv',tp='bt'  ,tid='kved' ,l=DLG_W-5-80   ,w=80           ,cap=_('Cha&nge')                           )] # &n
            )
            +([] if not as_file else []
                 +[dict(           tp='lb'  ,tid='kved' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kved',tp='ed'  ,t=65+LST_H ,l=l_val+5      ,w=COL_WS[-1]+15-30                                         )] #
                 +[dict(cid='brow',tp='bt'  ,tid='kved' ,l=DLG_W-5-80-35,w=30           ,cap=_('&...') ,hint=_('Browse file')       )] # &.
                 +[dict(cid='setv',tp='bt'  ,tid='kved' ,l=DLG_W-5-80   ,w=80           ,cap=_('Cha&nge')                           )] # &n
            )
            +([] if not as_enum else []
                 +[dict(           tp='lb'  ,tid='kvcb' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kvcb',tp='cb-ro',t=65+LST_H,l=l_val+5      ,w=COL_WS[-1]+15,items=var_sel                      ,act='1')] #
            )
                # View def-value
                 +[dict(           tp='lb'  ,tid='dfvl' ,l=l_val-100-5  ,w=100          ,cap=_('>Default value:')                   )] # 
                 +[dict(cid='dfvl',tp='ed'  ,t=93+LST_H ,l=l_val+5      ,w=COL_WS[-1]+15                        ,ro_mono_brd='1,0,1')] #
                 +[dict(cid='setd',tp='bt'  ,tid='dfvl' ,l=DLG_W-5-80   ,w=80           ,cap=_('Reset')                             )] # 
                # View commnent
                 +[dict(cid='cmnt',tp='memo',t=125+LST_H,l=5 ,h=CMNT_H-3,w=LST_W                                ,ro_mono_brd='1,1,1')] #

                 +[dict(cid='cust',tp='bt'  ,t=150      ,l=DLG_W-5-80   ,w=80           ,cap=_('Ad&just…')                          )] # &j
#                +[dict(cid='?'   ,tp='bt'  ,t=DLG_H-65 ,l=DLG_W-5-80   ,w=80           ,cap=_('&Help…')                            )] # &h
                 +[dict(cid='-'   ,tp='bt'  ,t=DLG_H-35 ,l=DLG_W-5-80   ,w=80           ,cap=_('Close')                             )] #
                 )
        vals    =       dict(cond=cond_s
                            ,lvls=ind_sel
                            ,dfvl=to_str(dvl_sel, frm_sel, dct_sel)     if key_sel else ''
                            ,cmnt=cmt_sel.replace('\r', '\n')           if key_sel else ''
                            )
        if 1<len(chap_l):
            vals.update(dict(chap=chap_n))
        if tags_l:
            vals.update(dict(tags=tags_n))
        if as_bool:
            vals.update(dict(kvbl=val_sel                               if key_sel else False))
        if as_char:
            vals.update(dict(kved=to_str(val_sel, frm_sel, dct_sel)     if key_sel else ''  ))
        if as_enum:
            vals.update(dict(kvcb=sel_sel                               if key_sel else False))

       #pass;                   LOG and log('cnts={}',(cnts))
        aid, vals, fid, chds = dlg_wrapper(f('{} ({})', title, VERSION_V), DLG_W, DLG_H, cnts, vals, focus_cid=fid)
        if aid is None or aid=='-':  return

        if aid=='fltr' and fid=='kved':     # Подмена умолчательной кнопки по активному редактору
            aid = 'setv'

        pass;                  #    LOG and log('aid={}',(aid))

        fid     = 'lvls'
        cond_s  = vals['cond']
        chap_n  = vals['chap']  if 1<len(chap_l)    else chap_n
        ind_sel = vals['lvls']

        stores[subset+'h.cond']= add_to_history(cond_s, stores.get(subset+'h.cond', []), MAX_HIST, unicase=False)
        stores[subset+'chap']  = chap_l[chap_n]
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))

        if aid=='cust':
            custs   = app.dlg_input_ex(6, _('Adjust')
                  , _(  'Height of Table (min 100)')  , str(stores.get(subset+'cust.ht_t', 100))
                  , _(     'Width of Key (min 250)')  , str(stores.get(subset+'cust.wd_k', 250))
                  , _(    'Width of Type (min  50)')  , str(stores.get(subset+'cust.wd_f',  50))
                  , _(       'Width of * (min  20)')  , str(stores.get(subset+'cust.wd_s',  20))
                  , _(   'Width of Value (min 250)')  , str(stores.get(subset+'cust.wd_v', 250))
                  , _('Height of Comment (min  55)')  , str(stores.get(subset+'cust.ht_c',  55))
                    )
            if custs is None:   continue#while
            stores[subset+'cust.ht_t']  = max(100, int(custs[0]))
            stores[subset+'cust.wd_k']  = max(250, int(custs[1]))
            stores[subset+'cust.wd_f']  = max( 50, int(custs[2]))
            stores[subset+'cust.wd_s']  = max( 20, int(custs[3]))
            stores[subset+'cust.wd_v']  = max(250, int(custs[4]))
            stores[subset+'cust.ht_c']  = max( 55, int(custs[5]))
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            continue#while
            
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

        if aid in ('kvbl', 'setv', 'kvcb', 'brow'):
            old_val = k2fdcvt[key_sel]['v']
            
            if aid=='kvbl':
                k2fdcvt[key_sel]['v'] = not k2fdcvt[key_sel]['v']
            if aid=='setv':
                new_val = vals['kved']
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
            if aid=='kvcb' and vals['kvcb']!=-1:
                ind     = vals['kvcb']
                k2fdcvt[key_sel]['v'] = list(dct_sel.keys())[ind]
            if aid=='brow':
                path    = app.dlg_file(True, '', os.path.expanduser(k2fdcvt[key_sel]['v']), '')
                if not path:  continue#while
                k2fdcvt[key_sel]['v'] = path

            new_val = k2fdcvt[key_sel]['v']
            if old_val != new_val:
                # Update json file
                apx.set_opt(key_sel, new_val)
            
       #while
   #def dlg_opt_editor

def parse_raw_keys_info(path_to_raw):
    pass;                       LOG and log('path_to_raw={}',(path_to_raw))
    #NOTE: parse_raw
    kinfs    = []
    lines   = open(path_to_raw, encoding='utf8').readlines()
    l       = '\n'
    
    reTags  = re.compile(r' *\((#\w+,?)+\)')
    reN2S   = re.compile(r' *(\d+): *(.+)')
    reS2S   = re.compile(r' *"(\w+)": *(.+)')
    def parse_cmnt(cmnt, frm):  
        tags= set()
        mt  = reTags.search(cmnt)
        while mt:
            tags_s  = mt.group(0)
            cmnt    = cmnt.replace(tags_s, '')
            mt      = reTags.search(cmnt)
            tags   |= set(tags_s.strip(' ()').replace('#', '').split(','))
        dctN= [[int(m.group(1)), m.group(2)] for m in reN2S.finditer(cmnt)]
        dctS= [[    m.group(1) , m.group(2)] for m in reN2S.finditer(cmnt)]
        frm,\
        dct = ('enum_i', dctN)    if dctN else \
              ('enum_s', dctS)    if dctS else \
              (frm     , []  )
        return cmnt, frm, dct, list(tags)
       #def parse_cmnt
    
    reChap  = re.compile(r' *//\[Section: +(.+)\]')
    reCmnt  = re.compile(r' *//(.+)')
    reKeyDV = re.compile(r' *"(\w+)" *: *(.+)')
    reFontNm= re.compile(r'font\w*_name')
    chap    = ''
    ref_cmnt= ''    # Full comment to add to '... smth'
    cmnt    = ''
    for line in lines:
        if False:pass
        elif    reChap.match(line):
            mt= reChap.match(line)
            chap    = mt.group(1)
            cmnt    = ''
        elif    reCmnt.match(line):
            mt= reCmnt.match(line)
            cmnt   += l+mt.group(1)
        elif    reKeyDV.match(line):
            cmnt    = cmnt.strip(l)
            mt= reKeyDV.match(line)
            key     = mt.group(1)
            dval_s  = mt.group(2).rstrip(',')
            frm,dval= ('int',  int(dval_s)  )   if dval_s.isdigit()                     else \
                      ('float',float(dval_s))   if dval_s.isdecimal()                   else \
                      ('bool', True         )   if dval_s=='true'                       else \
                      ('bool', False        )   if dval_s=='false'                      else \
                      ('font', dval_s[1:-1] )   if reFontNm.search(key)                 else \
                      ('str',  dval_s[1:-1] )   if dval_s[0]=='"' and dval_s[-1]=='"'   else \
                      ('unk',  dval_s       )
            
            ref_cmnt= ref_cmnt                                      if cmnt.startswith('...') else cmnt
            kinf    = OrdDict()
            kinfs  += [kinf]
            kinf['key']         = key
            kinf['def_val']     = dval
            cmnt,frm,dct,tags   = parse_cmnt(ref_cmnt+l+cmnt[3:]    if cmnt.startswith('...') else cmnt, frm)
            kinf['comment']     = cmnt
            if frm in ('enum_i','enum_s','font'):
                kinf['format']  = frm
            if dct:
                kinf['dct']     = dct
            if chap:
                kinf['chapter'] = chap
            if tags:
                kinf['tags']    = tags
            cmnt    = ''
       #for line
    
    return kinfs
   #def parse_raw_keys_info

def index_1(cllc, val, defans=-1):
    return cllc.index(val) if val in cllc else defans

if __name__ == '__main__' :     # Tests
    Command().show_dlg()    #??
        
'''
ToDo
[+][kv-kv][02apr17] History for cond
[ ][kv-kv][02apr17] ? Chapters list and "chap" attr into kinfo
[ ][kv-kv][02apr17] ? Tags list and "tag" attr into kinfo
[ ][kv-kv][02apr17] ? Delimeter row in table
[ ][kv-kv][02apr17] "Need restart" in Comments
[+][kv-kv][02apr17] ? Calc Format by Def_val
[ ][kv-kv][02apr17] int_mm for min+max
[+][kv-kv][02apr17] VERS in Title
[+][at-kv][02apr17] 'enum' вместо 'enum_i' 
[ ][kv-kv][02apr17] Save top row in table
[ ][kv-kv][03apr17] Show stat in Chap-combo and tags check-list
[ ][kv-kv][03apr17] ? Add chap "(No chapter)"
[ ][kv-kv][03apr17] ? Add tag "#no_tag"
[ ][kv-kv][03apr17] Call opts report
[+][at-kv][04apr17] Format 'font'
[-][at-kv][04apr17] ? FilterListView
[+][at-kv][04apr17] use new default.json
[ ][kv-kv][04apr17] Testing for update user.json
[+][kv-kv][04apr17] Restore Sec and Tags
[ ][kv-kv][04apr17] ro-combo hitory for Tags
[ ][kv-kv][05apr17] Add "default" to fonts if def_val=="default"
'''