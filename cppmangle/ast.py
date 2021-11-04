class _Enum(object):
    def __init__(self, desc):
        self.desc = desc

    def __repr__(self):
        return '{}({!r})'.format(__class__, self.__str__())

    def __str__(self):
        return self.desc

    def __eq__(self, other):
        if isinstance(other, _Enum):
            return self.desc == other.desc

        return False

    def __hash__(self):
        return self.desc.__hash__()

class Type(object):
    def __init__(self, cv):
        self.cv = cv

    def __repr__(self):
        return '{}({!r})'.format(__class__, self.__str__())

    def __str__(self):
        raise NotImplementedError()

    def __eq__(self, other):
        if isinstance(other, Type):
            return super().__eq__(other) and self.cv == other.cv

        return False

cv_none = 0
cv_const = 1
cv_volatile = 2

ptr64_name = '__ptr64 '
cv_names = ('', 'const ', 'volatile ', 'const volatile ')
class_kind_names = ('union', 'struct', 'class', 'enum')

class SimpleType(Type):
    def __init__(self, cv, basic_type):
        super().__init__(cv)
        self.basic_type = basic_type

    def __str__(self):
        return '{}{}'.format(cv_names[self.cv], str(self.basic_type))

    def __eq__(self, other):
        if isinstance(other, SimpleType):
            return self().__eq__(other) and self.basic_type == other.basic_type

        return False

class BasicType(_Enum):
    pass

t_none = BasicType('none')
t_void = BasicType('void')
t_bool = BasicType('bool')
t_char = BasicType('char')
t_schar = BasicType('signed char')
t_uchar = BasicType('unsigned char')
t_sshort = BasicType('short int')
t_ushort = BasicType('unsigned short')
t_sint = BasicType('int')
t_uint = BasicType('unsigned int')
t_slong = BasicType('long')
t_ulong = BasicType('unsigned long')
t_slonglong = BasicType('__int64')
t_ulonglong = BasicType('unsigned __int64')
t_wchar = BasicType('wchar_t')
t_float = BasicType('float')
t_double = BasicType('double')
t_longdouble = BasicType('long double')
t_ellipsis = BasicType('...')

class PtrType(Type):
    def __init__(self, cv, target, ref, addr_space):
        super().__init__(cv)
        self.target = target
        self.ref = ref
        self.addr_space = addr_space

    def __str__(self):
        return '{}{}'.format(str(self.target), '&' if self.ref else '*')

    def __eq__(self, other):
        if isinstance(other, PtrType):
            return super().__eq__(other) and self.target == other.target and self.ref == other.ref and self.addr_space == other.addr_space

        return False

k_union = 0
k_struct = 1
k_class = 2
k_enum = 3

class ClassType(Type):
    def __init__(self, cv, kind, qname, addr_space=None):
        super(ClassType, self).__init__(cv)
        self.kind = kind
        self.qname = qname

        # hack for 'modified' types denoted by '?'
        self.addr_space = addr_space

    def __str__(self):
        return '{}{}'.format(cv_names[self.cv], '::'.join(map(str, self.qname)))

    def __eq__(self, other):
        if isinstance(other, ClassType):
            return super().__eq__(other) and self.kind == other.kind and self.qname == other.qname and self.addr_space == other.addr_space

        return False

class FunctionType(Type):
    def __init__(self, cconv, ret_type, params, this_cv):
        super().__init__(cv_none)
        self.cconv = cconv
        self.ret_type = ret_type
        self.params = params
        self.this_cv = this_cv

    def __str__(self):
        return '{} __{}({}) {}'.format(
            self.ret_type,
            str(self.cconv),
            ', '.join(map(str, self.params)),
            cv_names[self.this_cv])

    def __eq__(self, other):
        if isinstance(other, FunctionType):
            return super().__eq__(other) and self.cconv == other.cconv and self.ret_type == other.ret_type and self.params == other.params and self.this_cv == other.this_cv

        return False

class ArrayType(Type):
    def __init__(self, dims, target):
        super().__init__(cv_none)
        self.dims = dims
        self.target = target

    def __eq__(self, other):
        if isinstance(other, ArrayType):
            return super().__eq__(other) and self.dims == other.dims and self.target == other.target

        return False

class Name(object):
    def __repr__(self):
        return '{}({!r})'.format(__class__, self.__str__())

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __str__(self):
        raise NotImplementedError()

    def __hash__(self):
        return self.__str__().__hash__()

class SpecialName(Name):
    def __init__(self, desc):
        self.desc = desc

    def __str__(self):
        return self.desc

class RTTIName(SpecialName):
    def __init__(self, desc, rtti_type):
        self.desc = desc
        self.rtti_type = rtti_type

class RTTITypeDescriptorName(RTTIName):
    def __init__(self, desc, type=None):
        super().__init__(desc, r_rtti_type_descriptor)
        self.type = type

class RTTIBaseClassDescriptorName(RTTIName):
    def __init__(self, desc, member_displacement=0, vftable_displacement=0, displacement_within_vftable=0, attributes=0):
        super().__init__(desc, r_rtti_base_class_descriptor)
        self.member_displacement = member_displacement
        self.vftable_displacement = vftable_displacement
        self.displacement_within_vftable = displacement_within_vftable
        self.attributes = attributes

    def __str__(self):
        return self.desc.format(
            self.member_displacement,
            self.vftable_displacement,
            self.displacement_within_vftable,
            self.attributes)

r_rtti_type_descriptor = 0
r_rtti_base_class_descriptor = 1
r_rtti_base_class_array = 2
r_rtti_class_hierarchy_descriptor = 3
r_rtti_complete_object_locator = 4

n_constructor = SpecialName("`constructor'")
n_def_constr_closure = SpecialName("`default constructor closure'")
n_destructor = SpecialName("`destructor'")
n_op_subscript = SpecialName("operator[]")
n_op_call = SpecialName("operator()")
n_op_member = SpecialName("operator->")
n_op_inc = SpecialName("operator++")
n_op_dec = SpecialName("operator--")
n_op_new = SpecialName("operator new")
n_op_new_arr = SpecialName("operator new[]")
n_op_delete = SpecialName("operator delete")
n_op_delete_arr = SpecialName("operator delete[]")
n_op_deref = SpecialName("operator*")
n_op_addr = SpecialName("operator&")
n_op_plus = SpecialName("operator+")
n_op_minus = SpecialName("operator-")
n_op_lnot = SpecialName("operator!")
n_op_bnot = SpecialName("operator~")
n_op_mem_ptr = SpecialName("operator->*")
n_op_mul = SpecialName("operator*")
n_op_div = SpecialName("operator/")
n_op_mod = SpecialName("operator%")
n_op_add = SpecialName("operator+")
n_op_sub = SpecialName("operator-")
n_op_shl = SpecialName("operator<<")
n_op_shr = SpecialName("operator>>")
n_op_lt = SpecialName("operator<")
n_op_gt = SpecialName("operator>")
n_op_le = SpecialName("operator<=")
n_op_ge = SpecialName("operator>=")
n_op_eq = SpecialName("operator==")
n_op_neq = SpecialName("operator!=")
n_op_band = SpecialName("operator&")
n_op_bor = SpecialName("operator|")
n_op_xor = SpecialName("operator^")
n_op_land = SpecialName("operator&&")
n_op_lor = SpecialName("operator||")
n_op_assign = SpecialName("operator=")
n_op_assign_mul = SpecialName("operator*=")
n_op_assign_div = SpecialName("operator/=")
n_op_assign_mod = SpecialName("operator%=")
n_op_assign_add = SpecialName("operator+=")
n_op_assign_sub = SpecialName("operator-=")
n_op_assign_shl = SpecialName("operator<<=")
n_op_assign_shr = SpecialName("operator>>=")
n_op_assign_band = SpecialName("operator&=")
n_op_assign_bor = SpecialName("operator|=")
n_op_assign_xor = SpecialName("operator^=")
n_op_comma = SpecialName("operator,")
n_op_cast = SpecialName("operator <cast>")
n_vftable = SpecialName("`vftable'")
n_vtable = n_vftable
n_vbtable = SpecialName("`vbtable'")
n_vcall = SpecialName("`vcall'")
n_typeof = SpecialName("`typeof'")
n_local_static_guard = SpecialName("`local static guard'")
n_vbase_destructor = SpecialName("`vbase destructor'")
n_vector_deleting_destructor = SpecialName("`vector deleting destructor'")
n_scalar_deleting_destructor = SpecialName("`scalar deleting destructor'")
n_vector_constructor_iterator = SpecialName("`vector constructor iterator'")
n_vector_destructor_iterator = SpecialName("`vector destructor iterator'")
n_vector_vbase_constructor_iterator = SpecialName("`vector vbase constructor iterator'")
n_virtual_displacement_map = SpecialName("`virtual displacement map'")
n_eh_vector_constructor_iterator = SpecialName("`eh vector constructor iterator'")
n_eh_vector_destructor_iterator = SpecialName("`eh vector destructor iterator'")
n_eh_vector_vbase_constructor_iterator = SpecialName("`eh vector vbase constructor iterator'")
n_copy_constructor_closure = SpecialName("`copy constructor closure'")
n_op_udt_returning = SpecialName("`udt returning'operator->")
n_rtti_type_descriptor = RTTITypeDescriptorName("`RTTI Type Descriptor'")
n_rtti_base_class_descriptor = RTTIBaseClassDescriptorName("`RTTI Base Class Descriptor at ({0}, {1}, {2}, {3})'")
n_rtti_base_class_arr = RTTIName("`RTTI Base Class Array'", r_rtti_base_class_array)
n_rtti_class_hierarchy_descriptor = RTTIName("`RTTI Class Hierarchy Descriptor'", r_rtti_class_hierarchy_descriptor)
n_rtti_complete_object_locator = RTTIName("`RTTI Complete Object Locator'", r_rtti_complete_object_locator)
n_local_vftable = SpecialName("`local vftable'")
n_local_vtable = n_local_vftable
n_local_vftable_constructor_closure = SpecialName("`local vftable constructor closure'")
n_local_vtable_constructor_closure = n_local_vftable_constructor_closure
n_omni_callsig = SpecialName("`omni callsig'")
n_placement_delete_closure = SpecialName("`placement delete closure'")
n_placement_delete_arr_closure = SpecialName("`placement delete[] closure'")
n_managed_vector_constructor_iterator = SpecialName("`managed vector constructor iterator'")
n_managed_vector_destructor_iterator = SpecialName("`managed vector destructor iterator'")
n_eh_vector_copy_constructor_iterator = SpecialName("`eh vector copy constructor iterator'")
n_eh_vector_vbase_copy_constructor_iterator = SpecialName("`eh vector vbase copy constructor iterator'")
n_dynamic_initializer = SpecialName("`dynamic initializer'")
n_dynamic_atexit_destructor = SpecialName("`dynamic atexit destructor'")
n_vector_copy_constructor_iterator = SpecialName("`vector copy constructor iterator'")
n_vector_vbase_copy_constructor_iterator = SpecialName("`vector vbase copy constructor iterator'")
n_managed_vector_copy_constructor_iterator = SpecialName("`managed vector copy constructor iterator'")
n_local_static_thread_guard = SpecialName("`local static thread guard'")
n_op_udf_literal = SpecialName("operator\"\"")

class TemplateId(Name):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __str__(self):
        return '{}<{}>'.format(self.name, ', '.join(map(str, self.args)))

class CallingConv(_Enum):
    pass
cconv_cdecl = CallingConv('cdecl')
cconv_stdcall = CallingConv('stdcall')
cconv_thiscall = CallingConv('thiscall')
cconv_fastcall = CallingConv('fastcall')

class AccessSpecifier(_Enum):
    pass
access_public = AccessSpecifier('public')
access_protected = AccessSpecifier('protected')
access_private = AccessSpecifier('private')

class FunctionKind(_Enum):
    pass
fn_free = FunctionKind('<free fn>')
fn_instance = FunctionKind('<non-static non-virtual member fn>')
fn_virtual = FunctionKind('<virtual member fn>')
fn_class_static = FunctionKind('<static member fn>')

class AddressSpace(_Enum):
    pass
as_default = AddressSpace('<default>')
as_msvc_x64_absolute = AddressSpace('absolute')

sc_private_static_member    = '0'
sc_protected_static_member  = '1'
sc_public_static_member     = '2'
sc_global                   = '3'
sc_static_local             = '4'
sc_static_guard             = '5'
sc_vftable                  = '6'
sc_vtable                   = sc_vftable
sc_vbtable                  = '7'
sc_rtti                     = '8'
sc_extern_c                 = '9'

class Symbol(object):
    def get_access_spec(self):
        pass

class Function(Symbol):
    def __init__(self, qname, type, kind, access_spec, addr_space):
        self.qname = qname
        self.type = type
        self.kind = kind
        self.access_spec = access_spec
        self.addr_space = addr_space

    def get_access_spec(self):
        return self.access_spec

class Variable(Symbol):
    def __init__(self, qname, ret_type=None, cv=cv_none, storage_class=None, addr_space=as_default):
        self.qname = qname
        self.ret_type = ret_type
        self.cv = cv
        self.storage_class = storage_class
        self.addr_space = addr_space

    def get_access_spec(self):
        if self.storage_class == sc_private_static_member:
            return access_private
        elif self.storage_class == sc_protected_static_member:
            return access_protected
        elif self.storage_class == sc_public_static_member:
            return access_public
        else:
            return None

