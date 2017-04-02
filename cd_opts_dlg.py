''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.0.0 2017-04-02'
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
MIN_API_VER = '1.0.168'
MAX_HIST    = apx.get_opt('ui_max_history_edits', 20)
CFG_JSON    = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_options_editor.json'


class Command:
    def dlg_cuda_opts(self):
        pass;                  #LOG and log('ok',())
        pass;                  #dlg_opt_editor('CudaText options', '')
        pass;                  #return 
#       cuda_opts   = apx.get_def_setting_dir()+os.sep+'default_options.json'
        cuda_opts   = os.path.dirname(__file__)+os.sep+'default_options.json'
        dlg_opt_editor('CudaText options', json.loads(open(cuda_opts).read()))
       #def dlg_cuda_opts
   #class Command

def dlg_opt_editor(title, keys_info, path_to_json='settings/user.json'):
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
    if -1== 1:  # Test data
        keys_info = [dict(key='key-bool',format='bool'  ,def_val=False           ,comment= 'smth')
                    ,dict(key='key-int' ,format='int'   ,def_val=123             ,comment= 'smth\nsmth')
                    ,dict(key='key-aint'                ,def_val=123             ,comment= 'smth\nsmth')
                    ,dict(key='key-str' ,format='str'   ,def_val='xyz'           ,comment= 'smth')
                    ,dict(key='key-flo' ,format='float' ,def_val=1.23            ,comment= 'smth')
                    ,dict(key='key-aflo'                ,def_val=1.23            ,comment= 'smth')
                    ,dict(key='key-file',format='file'  ,def_val=''              ,comment= 'smth')
                    ,dict(key='key-en_i',format='enum_i',def_val=1               ,comment= 'smth',   dct={0:'000', 1:'111', 2:'222'})
                    ,dict(key='key-en_s',format='enum_s',def_val='b'             ,comment= 'smth',   dct=[('a','AA'), ('b','BB'), ('c','CC')])
                    ,dict(key='key-json',format='json'  ,def_val={'x':{'a':1}}   ,comment= 'Style')
                    ]
        path_to_json=os.path.dirname(__file__)+os.sep+'test.json'

    if 0==len(keys_info):
        return app.msg_status(_('Empty keys_info'))

    stores      = json.loads(open(CFG_JSON).read(), object_pairs_hook=OrdDict) \
                    if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                  OrdDict()

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
        if kformat in ('enum_i', 'enum_s') and dct is not None:
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

    k2fdcvt = OrdDict([
            (       kinfo['key'],
               {'f':kinfo.get('format', frm_of_val(kinfo['def_val']))
               ,'t':kinfo.get('dct')            if ('dct' not in kinfo or   isinstance(kinfo.get('dct'), dict)) else 
                    OrdDict(kinfo.get('dct'))
               ,'d':kinfo['def_val']
               ,'c':kinfo['comment']            if                          isinstance(kinfo['comment'], str) else
                    '\n'.join(kinfo['comment'])
               ,'v':apx.get_opt(kinfo['key'], kinfo['def_val'])
               }
            )  for  kinfo in keys_info
            ])
    pass;                      #LOG and log('k2fdcvt={}',(k2fdcvt))

    key_sel = keys_info[0]['key']
    cond    = ''
    fid     = 'lvls'
    while True: #NOTE: json_props
        COL_WS      = [stores.get('cust.wd_k', 200)
                      ,stores.get('cust.wd_f', 50)
                      ,stores.get('cust.wd_s', 20)
                      ,stores.get('cust.wd_v', 450)]         # Widths of listview columns 
        CMNT_H      =  stores.get('cust.ht_c', 100)          # Height of Comment memo
        LST_W, LST_H= sum(COL_WS)+20 \
                    ,  stores.get('cust.ht_t', 200)-5        # Listview sizes
        DLG_W, DLG_H= 5+LST_W+5+80+5 \
                    , 5+20+30+LST_H+5+30+5+CMNT_H+5+3   # Dialog sizes
    
        fl_kfsvt= [ (knm
                    ,fdcv['f']
                    ,'!' if fdcv['d']!=fdcv['v'] else ''
                    ,fdcv['v']
                    ,fdcv['t']
                    )
                    for (knm, fdcv) in k2fdcvt.items()
                    if  cond=='' or cond.upper() in knm.upper() ]
        fl_k2i  = {knm:ikey for (ikey, (knm,kf,kset,kv,kdct)) in enumerate(fl_kfsvt)}
        ind_sel = fl_k2i[key_sel]       if key_sel in fl_k2i            else \
                  0                     if fl_k2i                       else \
                  -1
        key_sel = fl_kfsvt[ind_sel][0]  if ind_sel!=-1                  else ''
        frm_sel = k2fdcvt[key_sel]['f'] if key_sel                      else ''
        dct_sel = k2fdcvt[key_sel]['t'] if key_sel                      else None
        dvl_sel = k2fdcvt[key_sel]['d'] if key_sel                      else None
        val_sel = k2fdcvt[key_sel]['v'] if key_sel                      else None
        cmt_sel = k2fdcvt[key_sel]['c'] if key_sel                      else ''
        var_sel = dct_sel.values()      if frm_sel in ('enum_i', 'enum_s')    else None
        sel_sel = list(dct_sel.keys()).index(val_sel) \
                                        if frm_sel in ('enum_i', 'enum_s') and \
                                           val_sel in dct_sel.keys()    else -1
        
        itms    = (zip([_('Key'), _('Format'), _(' '), _('Value')], map(str, COL_WS))
                  ,    [ ( knm,      kf,          kset,   to_str(kv, kf, kdct)) for
                         ( knm,      kf,          kset,          kv,     kdct ) in fl_kfsvt]
                  )
        pass;                  #LOG and log('cond={}',(cond))
        pass;                  #LOG and log('fl_kfsvt={}',(fl_kfsvt))
        pass;                  #LOG and log('fl_k2i={}',(fl_k2i))
        pass;                  #LOG and log('key_sel,ind_sel={}',(key_sel, ind_sel))
        l_val   = DLG_W-10-80-20-COL_WS[-1]
        cnts    =([]
                 +[dict(           tp='lb'  ,t=5        ,l=5+2          ,w=COL_WS[0]    ,cap=_('&Filter:')                          )] # &k
                 +[dict(cid='ckey',tp='ed'  ,t=25       ,l=5+2          ,w=COL_WS[0]                                                )] #
                 +[dict(cid='fltr',tp='bt'  ,t=0        ,l=0            ,w=0            ,cap=''                 ,def_bt='1'         )] # 
                # View def-value
                 +[dict(           tp='lb'  ,t=5        ,l=l_val        ,w=COL_WS[-1]+20,cap=_('Default value:')                    )] # 
                 +[dict(cid='dfvl',tp='ed'  ,t=25       ,l=l_val        ,w=COL_WS[-1]+20                        ,ro_mono_brd='1,0,1')] #
                 +[dict(cid='setd',tp='bt'  ,tid='dfvl' ,l=DLG_W-5-80   ,w=80           ,cap=_('&Reset')                            )] # &r
                # Table
                 +[dict(cid='lvls',tp='lvw' ,t=55       ,l=5 ,h=LST_H   ,w=LST_W        ,items=itms             ,grid='1'   ,act='1')] #
            # Editors for value
            +([] if frm_sel not in ('bool') or not key_sel else []
                 +[dict(           tp='lb'  ,tid='kvbl' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kvbl',tp='ch'  ,t=65+LST_H ,l=l_val,w=COL_WS[-1]+20,cap=_('&Set')                              ,act='1')] #
            )
            +([] if frm_sel not in ('int', 'float', 'str', 'json') or not key_sel else []
                 +[dict(           tp='lb'  ,tid='kved' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kved',tp='ed'  ,t=65+LST_H ,l=l_val        ,w=COL_WS[-1]+20                                            )] #
                 +[dict(cid='setv',tp='bt'  ,tid='kved' ,l=DLG_W-5-80   ,w=80           ,cap=_('&Set')                              )] # &s
            )
            +([] if frm_sel not in ('file') or not key_sel else []
                 +[dict(           tp='lb'  ,tid='kved' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kved',tp='ed'  ,t=65+LST_H ,l=l_val        ,w=COL_WS[-1]+20-30                                         )] #
                 +[dict(cid='brow',tp='bt'  ,tid='kved' ,l=DLG_W-5-80-35,w=30           ,cap=_('&...') ,hint=_('Browse file')       )] # &.
                 +[dict(cid='setv',tp='bt'  ,tid='kved' ,l=DLG_W-5-80   ,w=80           ,cap=_('&Set')                              )] # &s
            )
            +([] if frm_sel not in ('enum_i', 'enum_s') or not key_sel else []
                 +[dict(           tp='lb'  ,tid='kvcb' ,l=l_val-100-5  ,w=100          ,cap=_('>&Value:')                          )] # &v 
                 +[dict(cid='kvcb',tp='cb-ro',t=65+LST_H,l=l_val,w=COL_WS[-1]+20,items=var_sel                              ,act='1')] #
            )
                # View commnent
                 +[dict(cid='cmnt',tp='memo',t=95+LST_H ,l=5 ,h=CMNT_H-3,w=LST_W                                ,ro_mono_brd='1,1,1')] #
                 +[dict(cid='cust',tp='bt'  ,t=55       ,l=DLG_W-5-80   ,w=80           ,cap=_('&Adjust…')                          )] # &a
                 +[dict(cid='?'   ,tp='bt'  ,t=DLG_H-65 ,l=DLG_W-5-80   ,w=80           ,cap=_('&Help…')                            )] # &h
                 +[dict(cid='-'   ,tp='bt'  ,t=DLG_H-35 ,l=DLG_W-5-80   ,w=80           ,cap=_('Close')                             )] #
                 )
        vals    =   dict(ckey=cond
                        ,lvls=ind_sel
                        ,dfvl=to_str(dvl_sel, frm_sel, dct_sel)     if key_sel else ''
                        ,cmnt=cmt_sel.replace('\r', '\n')           if key_sel else ''
                        )
        if frm_sel in ('bool') and key_sel:
            vals.update(
                    dict(kvbl=val_sel                               if key_sel else False
                        ))
        if frm_sel in ('int', 'float', 'str', 'json', 'file') and key_sel:
            vals.update(
                    dict(kved=to_str(val_sel, frm_sel, dct_sel)     if key_sel else ''
                        ))
        if frm_sel in ('enum_i', 'enum_s') and key_sel:
            vals.update(
                    dict(kvcb=sel_sel                               if key_sel else False
                        ))

        aid, vals, fid, chds = dlg_wrapper(f('{} ({})', title, VERSION_V), DLG_W, DLG_H, cnts, vals, focus_cid=fid)
        if aid is None or aid=='-':  return

        if aid=='fltr' and fid=='kved':     # Подмена умолчательной кнопки по активному редактору
            aid = 'setv'

        pass;                       LOG and log('aid={}',(aid))

        fid     = 'lvls'
        cond    = vals['ckey']
        ind_sel = vals['lvls']
        if ind_sel==-1:  continue#while
        key_sel = fl_kfsvt[ind_sel][0]
        pass;                  #LOG and log('cond={}',(cond))

            
        if aid=='cust':
            pass;                   LOG and log('?? cust',())
            custs   = app.dlg_input_ex(6, _('Customization')
                , _('Width of Key     (min 150)')  , str(stores.get('cust.wd_k', 200))
                , _('Width of Format  (min 100)')  , str(stores.get('cust.wd_f',  50))
                , _('Width of !       (min  30)')  , str(stores.get('cust.wd_s',  20))
                , _('Width of Value   (min 250)')  , str(stores.get('cust.wd_v', 450))
                , _('Heght of Table   (min 200)')  , str(stores.get('cust.ht_t', 100))
                , _('Heght of Comment (min  50)')  , str(stores.get('cust.ht_c', 200))
                )
            if custs is None:   continue#while
            stores['cust.wd_k']  = max(150, int(custs[0]))
            stores['cust.wd_f']  = max(100, int(custs[1]))
            stores['cust.wd_s']  = max( 30, int(custs[2]))
            stores['cust.wd_v']  = max(250, int(custs[3]))
            stores['cust.ht_c']  = max(200, int(custs[4]))
            stores['cust.ht_c']  = max( 50, int(custs[5]))
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            
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
                    new_val = app.dlg_input(f(_('Value for "{}" (format "{}")'), key_sel, k2fdcvt[key_sel]['f']), new_val)
                    if new_val is None:
                        break#while not good
                #while not good
            
        if aid=='kvcb' and vals['kvcb']!=-1:
            ind = vals['kvcb']
            k2fdcvt[key_sel]['v'] = list(dct_sel.keys())[ind]
            
        if aid=='brow':
            path    = app.dlg_file(True, '', os.path.expanduser(k2fdcvt[key_sel]['v']), '')
            if not path:  continue#while
            k2fdcvt[key_sel]['v'] = path
            
       #while
   #def dlg_opt_editor


if __name__ == '__main__' :     # Tests
    Command().show_dlg()    #??
        
'''
ToDo
[ ][kv-kv][02apr17] History for ed-vals
[ ][kv-kv][02apr17] ? Chapters list and "chap" attr into kinfo
[ ][kv-kv][02apr17] ? Tags list and "tag" attr into kinfo
[ ][kv-kv][02apr17] ? Delimeter row in table
[ ][kv-kv][02apr17] "Need restart" in Comments
[+][kv-kv][02apr17] ? Calc Format by Def_val
[ ][kv-kv][02apr17] int_mm for min+max
[+][kv-kv][02apr17] VERS in Title
[+][at-kv][02apr17] 'enum' вместо 'enum_i' 
'''