import speg
from .ast import *

def _transpose(m):
    return dict((m[k], k) for k in m)

_basic_type_map = {
    '@': t_none,
    'X': t_void,
    '_N': t_bool,
    'D': t_char,
    'C': t_schar,
    'E': t_uchar,
    'F': t_sshort,
    'G': t_ushort,
    'H': t_sint,
    'I': t_uint,
    'J': t_slong,
    'K': t_ulong,
    '_J': t_slonglong,
    '_K': t_ulonglong,
    '_W': t_wchar,
    'M': t_float,
    'N': t_double,
    'O': t_longdouble,
    'Z': t_ellipsis,
    }

_basic_type_map_inv = _transpose(_basic_type_map)

_cc_map = {
    'A': cconv_cdecl,
    'E': cconv_thiscall,
    'G': cconv_stdcall,
    'I': cconv_fastcall,
    }

_cc_map_inv = _transpose(_cc_map)

_class_kind_map = {
    'T': k_union,
    'U': k_struct,
    'V': k_class,
    'W4': k_enum,
    }
_class_kind_map_inv = _transpose(_class_kind_map)

_special_names_map = {
    '0': n_constructor,
    '1': n_destructor,
    '2': n_op_new,
    '3': n_op_delete,
    '4': n_op_assign,
    '5': n_op_shr,
    '6': n_op_shl,
    '7': n_op_lnot,
    '8': n_op_eq,
    '9': n_op_neq,
    'A': n_op_subscript,
    'B': n_op_cast,
    'C': n_op_member,
    'D': n_op_deref,
    'D': n_op_mul,
    'E': n_op_inc,
    'F': n_op_dec,
    'G': n_op_sub,
    'H': n_op_add,
    'I': n_op_band,
    'J': n_op_mem_ptr,
    'K': n_op_div,
    'L': n_op_mod,
    'M': n_op_lt,
    'N': n_op_le,
    'O': n_op_gt,
    'P': n_op_ge,
    'Q': n_op_comma,
    'R': n_op_call,
    'S': n_op_bnot,
    'T': n_op_xor,
    'U': n_op_bor,
    'V': n_op_land,
    'W': n_op_lor,
    'X': n_op_assign_mul,
    'Y': n_op_assign_add,
    'Z': n_op_assign_sub,
    '_0': n_op_assign_div,
    '_1': n_op_assign_mod,
    '_2': n_op_assign_shr,
    '_3': n_op_assign_shl,
    '_4': n_op_assign_band,
    '_5': n_op_assign_bor,
    '_6': n_op_assign_xor,
    '_7': n_vftable,
    '_8': n_vbtable,
    '_9': n_vcall,
    '_A': n_typeof,
    '_B': n_local_static_guard,
    # '_C': None, # string constant
    '_D': n_vbase_destructor,
    '_E': n_vector_deleting_destructor,
    '_F': n_def_constr_closure,
    '_G': n_scalar_deleting_destructor,
    '_H': n_vector_constructor_iterator,
    '_I': n_vector_destructor_iterator,
    '_J': n_vector_vbase_constructor_iterator,
    '_K': n_virtual_displacement_map,
    '_L': n_eh_vector_constructor_iterator,
    '_M': n_eh_vector_destructor_iterator,
    '_N': n_eh_vector_vbase_constructor_iterator,
    '_O': n_copy_constructor_closure,
    '_P': n_op_udt_returning,
    # '_R': None, # RTTI
    '_S': n_local_vftable,
    '_T': n_local_vftable_constructor_closure,
    '_U': n_op_new_arr,
    '_V': n_op_delete_arr,
    '_W': n_omni_callsig,
    '_X': n_placement_delete_closure,
    '_Y': n_placement_delete_arr_closure,
    '__A': n_managed_vector_constructor_iterator,
    '__B': n_managed_vector_destructor_iterator,
    '__C': n_eh_vector_copy_constructor_iterator,
    '__D': n_eh_vector_vbase_copy_constructor_iterator,
    '__E': n_dynamic_initializer,
    '__F': n_dynamic_atexit_destructor,
    '__G': n_vector_copy_constructor_iterator,
    '__H': n_vector_vbase_copy_constructor_iterator,
    '__I': n_managed_vector_copy_constructor_iterator,
    '__J': n_local_static_thread_guard,
    '__K': n_op_udf_literal
    }

_special_names_map_inv = _transpose(_special_names_map)
_special_names_rtti_map = {
    '0': n_rtti_type_descriptor,
    '1': n_rtti_base_class_descriptor,
    '2': n_rtti_base_class_arr,
    '3': n_rtti_class_hierarchy_descriptor,
    '4': n_rtti_complete_object_locator
    }

def _p_simple_name(p):
    nl = p.get('names')
    with p:
        ref = int(p(r'\d'))
        return nl[ref]

    with p:
        special_name = p(r'\?_{0,2}[0-9A-Z]')[1:]
        if special_name == '_R':
            return _p_rtti_name(p)

        return _special_names_map[special_name]

    n = p(r'[^@]+@')[:-1]
    if n not in nl:
        p.set_global('names', nl + (n,))
    return n

def _p_rtti_name(p):
    rtti_type = p('[0-4]')
    ret = _special_names_rtti_map[rtti_type]

    if isinstance(ret, RTTITypeDescriptorName):
        type, _ = _p_type(p)
        return RTTITypeDescriptorName(ret.desc, type)
    elif isinstance(ret, RTTIBaseClassDescriptorName):
        return RTTIBaseClassDescriptorName(ret.desc, _p_int(p), _p_int(p), _p_int(p),  _p_int(p))

    return ret

def _p_int(p):
    neg = bool(p.opt(r'\?'))

    dig = p.opt(r'\d')
    if dig:
        r = int(dig) + 1
    else:
        t = p('[A-P]+@')[:-1]
        r = 0
        for ch in t:
            r = 16*r + (ord(ch) - ord('A'))

    return -r if neg else r

def _p_name(p):
    with p:
        p(r'\?\$')
        name = p(_p_simple_name)

        type_args = []
        while not p.opt('@'):
            if p.opt(r'\$0'):
                type_args.append(p(_p_int))
            else:
                arg, _ = p(_p_type)
                type_args.append(arg)
        return TemplateId(name, type_args)
    return p(_p_simple_name)

def _p_qname(p):
    qname = []
    with p:
        while not p.opt('@'):
            qname.append(p(_p_name))
            p.commit()
    return tuple(qname[::-1])

def _p_basic_type(p):
    c = p(r'[@XDCEFGHIJKMNOZ]|_[NJKW]')
    return SimpleType(0, _basic_type_map[c]), len(c) >= 2

_cvs = [cv_none, cv_const, cv_volatile, cv_const | cv_volatile]

def _p_type(p):
    addr_space = as_default
    target_cv = cv_none

    # check for modified types
    # this should really only be used situationally
    if p(r'[\?]?'):
        addr_space, target_cv = _p_get_modifier(p)

    with p:
        kind = p('T|U|V|W4')[0]
        kind = ord(kind) - ord('T')
        qname = p(_p_qname)
        return ClassType(target_cv, kind, qname, addr_space), True

    with p:
        # arrays
        p('Y')
        dim_count = p(_p_int)
        dims = tuple(p(_p_int) for i in xrange(dim_count))
        target, reg = p(_p_type)
        return ArrayType(dims, target), True

    with p:
        # pointer to fn
        cv = _cvs[ord(p('[PQRS]6')[0]) - ord('P')]
        fn_type = p(_p_fn_type)
        return PtrType(cv, fn_type, False, addr_space), True

    with p:
        # pointer types
        kind = p('[APQRS]')
        addr_space, target_cv = _p_get_modifier(p)

        target, reg = p(_p_type)
        target.cv = target_cv

        cv = _cvs[ord(kind) - ord('P')] if kind != 'A' else 0
        return PtrType(cv, target, kind == 'A', addr_space), True

    return p(_p_basic_type)

def _is_void_or_ellipsis(type):
    return isinstance(type, SimpleType) and type.basic_type in (t_void, t_ellipsis)

def _p_fn_type(p):
    cconv = _cc_map[p('[AEGI]')] #if qname[-1] not in _noncv_member_funcs else cconv_thiscall

    ret_cv = p(r'(\?[A-D])?')
    ret, reg = p(_p_type)
    if ret_cv:
        ret.cv = ord(ret_cv[1]) - ord('A')
    params = []

    with p:
        while not p.opt('@'):
            with p:
                reg_ref = p('\d')
                param_type = p.get('param_types')[int(reg_ref)]

            if not p:
                param_type, reg = p(_p_type)
                if reg:
                    param_types = p.get('param_types') + (param_type,)
                    p.set_global('param_types', param_types)

            params.append(param_type)
            p.commit()
            if _is_void_or_ellipsis(param_type):
                break

    p('Z')
    return FunctionType(cconv, ret, params, 0)

def _p_root(p):
    p.set_global('names', ())
    p.set_global('param_types', ())

    p(r'\?')
    qname = p(_p_qname)

    # consume class specifier if applicable
    # TODO: handle me properly
    p('@?')

    with p:
        return _p_root_function(p, qname)

    with p:
        return _p_root_variable(p, qname)

    raise RuntimeError('Unknown symbol type')

def _p_root_function(p, qname):
    # non-member function
    if p('[YZ]?'):
        access_class = None
        kind = fn_free
    # member function
    else:
        modif = p('[A-V]')
        modif = ord(modif) - ord('A')
        access_class = (access_private, access_protected, access_public)[modif // 8]
        modif = modif % 8
        if modif in (2, 3):
            kind = fn_class_static
        elif modif in (4, 5):
            kind = fn_virtual
        else:
            kind = fn_instance

    can_have_cv = kind in (fn_instance, fn_virtual)
    if can_have_cv:
        addr_space, this_cv = _p_get_modifier(p)
    else:
        addr_space = as_default
        this_cv = None

    type = p(_p_fn_type)
    p(p.eof)

    type.this_cv = this_cv

    return Function(qname, type, kind, access_class, addr_space)

def _p_root_variable(p, qname):
    ret = Variable(qname)
    ret.storage_class = p('[0-9]')

    # >= sc_private_static_member <= sc_static_local
    if ret.storage_class >= '0' and ret.storage_class <= '5':
        ret.ret_type, _ = p(_p_type)
        ret.addr_space, ret.cv = _p_get_modifier(p)
    elif ret.storage_class == sc_vftable or ret.storage_class == sc_vbtable:
        ret.addr_space, ret.cv = _p_get_modifier(p)
        is_structor = True if p(r'[@]?') else False
        if not is_structor:
            ret.ret_type, _ = p(_p_type)

    p(p.eof)
    return ret

def _p_get_modifier(p):
    addr_space = as_msvc_x64_absolute if p('E?') else as_default
    cv = ord(p('[A-D]')) - ord('A')
    return addr_space, cv

def msvc_demangle(s):
    return speg.peg(s, _p_root)

def _m_int(arg):
    r = []
    if arg < 0:
        r.append('?')
        arg = -arg

    if 1 <= arg <= 10:
        r.append(str(arg - 1))
    elif arg == 0:
        r.append('A@')
    else:
        digs = []
        while arg != 0:
            digs.append('ABCDEFGHIJKLMNOP'[arg % 16])
            arg = arg // 16
        digs.reverse()
        r.extend(digs)
        r.append('@')
    return ''.join(r)

def _m_templ_arg(arg):
    if isinstance(arg, int):
        return '$0{}'.format(_m_int(arg))
    return _m_type(arg, {}, {})

def _m_qname(qname, nl):
    r = []
    for name in qname[::-1]:
        pos = nl.get(name)
        if pos is not None:
            r.append(str(pos))
            continue

        if isinstance(name, RTTIBaseClassDescriptorName):
            r.append('?_R{}{}{}{}{}'.format(
                name.rtti_type,
                _m_int(name.member_displacement),
                _m_int(name.vftable_displacement),
                _m_int(name.displacement_within_vftable),
                _m_int(name.attributes)))
        elif isinstance(name, RTTITypeDescriptorName):
            r.append('?_R{}{}'.format(
                name.rtti_type,
                _m_type(name.type, nl, {})))
        elif isinstance(name, RTTIName):
            r.append('?_R{}'.format(name.rtti_type))
        elif isinstance(name, SpecialName):
            r.append('?{}'.format(_special_names_map_inv[name]))
        elif isinstance(name, TemplateId):
            r.append('?${}@{}@'.format(name.name, ''.join(_m_templ_arg(arg) for arg in name.args)))
        else:
            r.append('{}@'.format(name))
            if len(nl) < 9:
                nl[name] = len(nl)

    return '{}@'.format(''.join(r))

def _m_addr_space(addr_space):
    return 'E' if addr_space == as_msvc_x64_absolute else ''

def _m_cv(cv):
    return 'ABCD'[cv]

def _m_type(type, nl, tl):
    if isinstance(type, SimpleType):
        return _basic_type_map_inv[type.basic_type]
    if isinstance(type, PtrType):
        if type.ref:
            kind = 'A'
        else:
            kind = 'PQRS'[type.cv]
        if isinstance(type.target, FunctionType):
            return '{}6{}'.format(kind, _m_fn_type(type.target, nl, tl))
        else:
            return '{}{}{}{}'.format(kind, _m_addr_space(type.addr_space), _m_cv(type.target.cv), _m_type(type.target, nl, tl))
    if isinstance(type, ArrayType):
        return 'Y{}{}{}'.format(_m_int(len(type.dims)), ''.join(_m_int(dim) for dim in type.dims), _m_type(type.target, nl, tl))
    if isinstance(type, ClassType):
        qname = _m_qname(type.qname, nl)

        # check for modified types - there MUST be a way to do this better
        # it feels like it should just be for ClassTypes but this doesn't appear to be the case
        prefix = ''
        if type.addr_space is not None:
            prefix += '?{}{}'.format(_m_addr_space(type.addr_space), _m_cv(type.cv))

        return '{}{}{}'.format(prefix, _class_kind_map_inv[type.kind], qname)
    raise RuntimeError('whoops')

def _m_fn_type(type, nl, tl):
    cconv = _cc_map_inv[type.cconv]

    if isinstance(type.ret_type, ClassType):
        ret_cv = '?{}'.format('ABCD'[type.ret_type.cv])
    else:
        ret_cv = ''

    ret = '{}{}'.format(ret_cv, _m_type(type.ret_type, nl, tl))

    params = []
    for param in type.params:
        cannon = _m_type(param, {}, {})
        if len(cannon) == 1:
            params.append(cannon)
            continue

        ref = tl.get(cannon)
        if ref is not None:
            params.append(str(ref))
            continue

        p = _m_type(param, nl, tl)
        params.append(p)
        if len(tl) < 9:
            tl[cannon] = len(tl)

    term = '' if type.params and _is_void_or_ellipsis(type.params[-1]) else '@'
    return '{}{}{}{}Z'.format(cconv, ret, ''.join(params), term)

def msvc_mangle(obj):
    nl = {}
    tl = {}
    if isinstance(obj, Function):
        qname = _m_qname(obj.qname, nl)
        type = _m_fn_type(obj.type, nl, tl)

        if obj.kind == fn_free:
            modif = 'Y'
        else:
            if obj.kind == fn_class_static:
                modif = 2
            elif obj.kind == fn_virtual:
                modif = 4
            else:
                modif = 0

            if obj.access_spec == access_protected:
                modif += 8
            elif obj.access_spec == access_public:
                modif += 16

            modif = chr(ord('A') + modif)

        can_have_cv = obj.kind in (fn_instance, fn_virtual)
        addr_space = _m_addr_space(obj.addr_space) if can_have_cv else ''
        this_cv = _m_cv(obj.type.this_cv) if can_have_cv else ''

        return '?{}{}{}{}{}'.format(qname, modif, addr_space, this_cv, type)

    elif isinstance(obj, Variable):
        qname = _m_qname(obj.qname, nl)
        ret = '?{}{}'.format(qname, obj.storage_class)

        ret_cv = ''
        ret_type = '@'

        if obj.cv is not None:
            ret_cv = _m_addr_space(obj.addr_space)
            ret_cv += _m_cv(obj.cv)

        if obj.ret_type is not None:
            ret_type = _m_type(obj.ret_type, nl, tl)

        if obj.storage_class >= '0' and obj.storage_class <= '5':
            ret += '{}{}'.format(ret_type, ret_cv)
        elif obj.storage_class == sc_vftable or obj.storage_class == sc_vbtable:
            ret += '{}{}'.format(ret_cv, ret_type)

        return ret

    raise RuntimeError('unknown obj')
