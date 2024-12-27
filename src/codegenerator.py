import logging, os, urllib, traceback, textwrap, keyword
import xmlreg
from OpenGL._bytes import as_8_bit, as_str, unicode, as_unicode

HERE = os.path.join(os.path.dirname(__file__))
log = logging.getLogger(__name__)
AUTOGENERATION_SENTINEL = (
    """### DO NOT EDIT above the line "END AUTOGENERATED SECTION" below!"""
)
AUTOGENERATION_SENTINEL_END = """### END AUTOGENERATED SECTION"""


def nameToPathMinusGL(name):
    return "/".join(name.split('_', 2)[1:])


def prefix_split(name):
    return name.split('_', 2)[1:]


def indent(text, indent='\t'):
    return "\n".join(['%s%s' % (indent, line) for line in text.splitlines()])


class Generator(object):
    targetDirectory = os.path.join(HERE, '..', 'OpenGL')
    rawTargetDirectory = os.path.join(HERE, '..', 'OpenGL', 'raw')
    prefix = 'GL'
    dll = '_p.PLATFORM.GL'
    includeOverviews = True

    def __init__(self, registry, type_translator):
        self.registry = registry
        self.type_translator = type_translator

    def module(self, module):
        if hasattr(module, 'apis'):
            for api in module.apis:
                if api != 'glcore':
                    gen = ModuleGenerator(module, self, api)
                    gen.generate()
        else:
            gen = ModuleGenerator(module, self)
            gen.generate()
        return gen

    GLGET_PARAM_GROUPS = [
        #'MaterialParameter',
        #'PixelMap',
        #'LightParameter',
        'GetPName',
        #'GetPixelMap',
        #'GetMapQuery',
        'GetPointervPName',
        #'TextureEnvParameter',
        #'TextureGenParameter',
    ]
    GL_GET_TEMPLATE = '''"""glGet* auto-generation of output arrays (DO NOT EDIT, AUTOGENERATED)"""
try:
    from OpenGL.raw.%(prefix)s._lookupint import LookupInt as _L
except ImportError:
    def _L(*args):
        raise RuntimeError( "Need to define a lookupint for this api" )
_glget_size_mapping = _m = {}
%(elements)s
'''

    def group_sizes(self):
        """Generate a group-sizes data-table for the given group-name"""
        result = []
        for enum_name, size in sorted(
            self.glGetSizes.items(), key=lambda x: (bool(x[1]), x[0])
        ):
            value = self.registry.enumeration_set.get(enum_name)
            size = [x for x in size if x]
            comment = ''
            if not size:
                size = 'TODO'
                comment = '# '
            else:
                size = ''.join(size)
            if value is None:
                # common in cases where GL and GLES constants are updated together...
                log.debug('Unrecognized constant: %s in GLGet section', enum_name)
            else:
                value = value.value
                result.append(
                    '%(comment)s_m[%(value)s] = %(size)s # %(enum_name)s' % locals()
                )
        elements = '\n'.join(result)
        prefix = self.prefix
        return self.GL_GET_TEMPLATE % locals()

    def enum(self, enum):
        comment = ''
        try:
            int(enum.value, 0)
        except ValueError:
            comment = '# '
        return '%s%s=_C(%r,%s)' % (comment, enum.name, enum.name, enum.value)

    def safe_name(self, name):
        if keyword.iskeyword(name):
            return name + '_'
        return name

    def function(self, function):
        """Produce a declaration for this function in ctypes format"""
        returnType = self.type_translator(function.returnType)
        if returnType == 'arrays.GLbyteArray':
            returnType = 'ctypes.c_char_p'
        if function.argTypes:
            argTypes = ','.join([self.type_translator(x) for x in function.argTypes])
        else:
            argTypes = ''
        if function.argNames:
            argNames = ','.join([self.safe_name(n) for n in function.argNames])
        else:
            argNames = ''
        arguments = ', '.join(
            [
                '%s %s' % (t, self.safe_name(n))
                for (t, n) in zip(function.argTypes, function.argNames)
            ]
        )
        name = function.name
        if returnType.strip() in ('_cs.GLvoid', '_cs.void', 'void'):
            returnType = pyReturn = 'None'
        else:
            pyReturn = function.returnType
        doc = '%(name)s(%(arguments)s) -> %(pyReturn)s' % locals()
        #        log.info( '%s', doc )
        formatted = self.FUNCTION_TEMPLATE % locals()
        return formatted

    FUNCTION_TEMPLATE = """@_f
@_p.types(%(returnType)s,%(argTypes)s)
def %(name)s(%(argNames)s):pass"""

    _glGetSizes = None

    @property
    def glGetSizes(self):
        if self._glGetSizes is None:
            self._glGetSizes = self.loadGLGetSizes()
        return self._glGetSizes

    def loadGLGetSizes(self):
        """Load manually-generated table of glGet* sizes"""
        table = {}
        try:
            lines = [
                line.split('\t')
                for line in open(os.path.join(HERE, 'glgetsizes.csv'))
                .read()
                .splitlines()
            ]
        except IOError:
            pass
        else:
            for line in lines:
                if line and line[0]:
                    value = [v for v in [v.strip('"') for v in line[1:]] if v]
                    if value:
                        table[line[0].strip('"').strip()] = value
        # now make sure everything registered in the xml file is present...
        output_group_names = {}
        for function in self.registry.command_set.values():
            output_group_names.update(function.output_groups)
        for output_group in output_group_names.keys():
            log.debug('Output parameter group: %s', output_group)
            for name in self.registry.enum_groups.get(output_group, []):
                if name not in table:
                    log.info('New %s value: %r', output_group, name)
                    table[name] = ''
        return table

    def saveGLGetSizes(self):
        """Save out sorted list of glGet sizes to disk"""
        items = list(self.glGetSizes.items())
        items.sort()
        data = "\n".join(['%s\t%s' % (key, "\t".join(value)) for (key, value) in items])
        open(os.path.join(HERE, 'glgetsizes.csv'), 'w').write(data)


class ModuleGenerator(object):
    ROOT_EXTENSION_SOURCE = 'http://www.opengl.org/registry/specs/'
    RAW_MODULE_TEMPLATE = """'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.%(prefix)s import _types as _cs
# End users want this...
from OpenGL.raw.%(prefix)s._types import *
from OpenGL.raw.%(prefix)s import _errors
from OpenGL.constant import Constant as _C
%(extra_imports)s
import ctypes
_EXTENSION_NAME = %(constantModule)r
def _f( function ):
    return _p.createFunction( function,%(dll)s,%(constantModule)r,error_checker=_errors._error_checker)
%(constants)s
%(declarations)s
"""

    INIT_TEMPLATE = """
def glInit%(camelModule)s%(owner)s():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )
"""
    FINAL_MODULE_TEMPLATE = """'''OpenGL extension %(owner)s.%(module)s

This module customises the behaviour of the 
OpenGL.raw.%(prefix)s.%(owner)s.%(module)s to provide a more 
Python-friendly API

%(overview)sThe official definition of this extension is available here:
%(ROOT_EXTENSION_SOURCE)s%(owner)s/%(module)s.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.%(prefix)s import _types, _glgets
from OpenGL.raw.%(prefix)s.%(owner)s.%(module)s import *
from OpenGL.raw.%(prefix)s.%(owner)s.%(module)s import _EXTENSION_NAME
%(init_function)s
%(output_wrapping)s
"""
    dll = '_p.PLATFORM.GL'

    def __init__(self, registry, overall, api=None):
        self.registry = registry
        self.overall = overall
        name = registry.name
        if name in ('GL_ES_VERSION_3_1', 'GL_ES_VERSION_3_0'):
            api = 'gles3'
            name = 'GLES3' + name[5:]
        if api:
            self.prefix = api.upper()
        else:
            if hasattr(self.registry, 'api'):
                self.prefix = self.registry.api.upper()
            else:
                self.prefix = name.split('_')[0]
        name = name.split('_', 1)[1]
        try:
            self.owner, self.module = name.split('_', 1)
            self.sentinelConstant = '%s_%s' % (self.owner, self.module)

        except ValueError:
            if name.endswith('SGIX'):
                self.prefix = "GL"
                self.owner = 'SGIX'
                self.module = name[3:-4]
                self.sentinelConstant = '%s%s' % (self.module, self.owner)
            else:
                log.error("""Unable to parse module name: %s""", name)
                raise
        self.dll = '_p.PLATFORM.%s' % (self.prefix,)
        if self.module[0].isdigit():
            self.module = '%s_%s' % (
                self.prefix,
                self.module,
            )
        if self.module == 'async':
            self.module = 'async_'
        self.camelModule = "".join([x.title() for x in self.module.split('_')])
        self.rawModule = self.module

        self.rawOwner = self.owner
        while self.owner and self.owner[0].isdigit():
            self.owner = self.owner[1:]
        self.rawPathName = os.path.join(
            self.overall.rawTargetDirectory,
            self.prefix,
            self.owner,
            self.module + '.py',
        )
        self.pathName = os.path.join(
            self.overall.targetDirectory, self.prefix, self.owner, self.module + '.py'
        )

        self.constantModule = '%(prefix)s_%(owner)s_%(rawModule)s' % self
        specification = self.getSpecification()
        self.constantsFromSpec()
        self.overview = ''
        if self.overall.includeOverviews:
            for title, section in specification.blocks(specification.source):
                if title.startswith('Overview'):
                    if isinstance(section, bytes):
                        section = section.decode(
                            'latin-1'
                        )  # seems not to be utf in at lest some cases
                    self.overview = 'Overview (from the spec)\n%s\n\n' % (
                        indent(
                            as_unicode(
                                as_str(section)
                                .replace('\xd4', 'O')
                                .replace('\xd5', 'O')
                            )
                            .encode('ascii', 'ignore')
                            .decode('ascii', 'ignore')
                        )
                    )
                    break

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __getattr__(self, key):
        if key not in ('registry',):
            return getattr(self.registry, key)

    @property
    def extra_imports(self):
        if self.name == 'GL_VERSION_1_1':
            # spec files have not properly separated out these two...
            return '# Spec mixes constants from 1.0 and 1.1\nfrom OpenGL.raw.GL.VERSION.GL_1_0 import *'
        return ''

    def constantsFromSpec(self, spec=None):
        """Examine spec text looking for new constants..."""
        spec = spec or self.getSpecification()
        if spec.source:
            table = self.overall.glGetSizes
            extras = spec.glGetConstants()
            changed = False
            for key, value in extras.items():
                if key not in table:
                    try:
                        value = int(value, 16)
                    except ValueError:
                        continue
                    short_key = '_'.join(key.split("_")[:-1])
                    if short_key in table:
                        short_def = self.overall.registry.enumeration_set.get(short_key)
                        if short_def and int(short_def.value, 16) == value:
                            key = short_def.name
                    if not key in table:
                        table[key] = ['(1,)', '#TODO Review %s' % (self.specFile())]
                        changed = True
            if changed:
                self.overall.saveGLGetSizes()

    def shouldReplace(self):
        """Should we replace the given filename?"""
        filename = self.pathName
        if not os.path.isfile(filename):
            return True
        else:
            hasLines = 0
            for line in open(filename):
                if line.strip() == AUTOGENERATION_SENTINEL_END.strip():
                    return True
                hasLines = 1
            if not hasLines:
                return True
            log.warning(
                'Not replacing %s (no AUTOGENERATION_SENTINEL_END found)', filename
            )
        return False

    @property
    def output_wrapping(self):
        """Generate output wrapping statements for our various functions"""
        try:
            statements = []
            for function in self.registry.commands():
                dependencies = function.size_dependencies
                if dependencies:  # temporarily just do single-output functions...
                    base = []
                    for param, dependency in sorted(dependencies.items()):
                        param = as_str(param)
                        if isinstance(dependency, xmlreg.Output):
                            statements.append(
                                '# %s.%s is OUTPUT without known output size'
                                % (
                                    function.name,
                                    param,
                                )
                            )
                        if isinstance(dependency, xmlreg.Staticsize):
                            base.append(
                                '.setOutput(\n    %(param)r,size=(%(dependency)r,),orPassIn=True\n)'
                                % locals()
                            )
                        elif isinstance(dependency, xmlreg.Dynamicsize):
                            base.append(
                                '.setOutput(\n    %(param)r,size=lambda x:(x,),pnameArg=%(dependency)r,orPassIn=True\n)'
                                % locals()
                            )
                        elif isinstance(dependency, xmlreg.Multiple):
                            pname, multiple = dependency
                            base.append(
                                '.setOutput(\n    %(param)r,size=lambda x:(x,%(multiple)s),pnameArg=%(pname)r,orPassIn=True\n)'
                                % locals()
                            )
                        elif isinstance(dependency, xmlreg.Compsize):
                            if len(dependency) == 1:
                                pname = dependency[0]
                                base.append(
                                    '.setOutput(\n    %(param)r,size=_glgets._glget_size_mapping,pnameArg=%(pname)r,orPassIn=True\n)'
                                    % locals()
                                )
                            else:
                                statements.append(
                                    '# OUTPUT %s.%s COMPSIZE(%s) '
                                    % (function.name, param, ', '.join(dependency))
                                )
                        elif isinstance(dependency, xmlreg.StaticInput):
                            base.append(
                                '.setInputArraySize(\n    %(param)r, %(dependency)s\n)'
                                % locals()
                            )
                        elif isinstance(
                            dependency,
                            (xmlreg.DynamicInput, xmlreg.MultiplyInput, xmlreg.Input),
                        ):
                            if dependency is None:
                                continue
                            statements.append(
                                '# INPUT %s.%s size not checked against %s'
                                % (function.name, param, dependency)
                            )
                            base.append(
                                '.setInputArraySize(\n    %(param)r, None\n)' % locals()
                            )
                    if base:
                        base.insert(
                            0, '%s=wrapper.wrapper(%s)' % (function.name, function.name)
                        )
                        statements.append(''.join(base))
            return '\n'.join(statements)
        except Exception as err:
            traceback.print_exc()
            import pdb

            pdb.set_trace()

    def get_constants(self):
        functions = self.registry.enums()
        functions.sort(key=lambda x: x.name)
        return functions

    @property
    def init_function(self):
        return self.INIT_TEMPLATE % self

    @property
    def constants(self):
        result = []
        try:
            for function in self.get_constants():
                result.append(self.overall.enum(function))
            return '\n'.join(result)
        except Exception:
            traceback.print_exc()
            raise

    @property
    def declarations(self):
        functions = self.registry.commands()
        functions.sort(key=lambda x: x.name)
        result = []
        for function in functions:
            result.append(self.overall.function(function))
        return "\n".join(result)

    EXTENSION_BASE = os.path.join(HERE, 'khronosapi', 'extensions')

    def specFile(self):
        """Lookup the specification file for our extension"""
        prefix, name = prefix_split(self.name)
        specFile = os.path.join(
            self.EXTENSION_BASE,
            prefix,
            '%s_%s.txt'
            % (
                prefix,
                name,
            ),
        )
        return specFile

    def getSpecification(self):
        """Retrieve our specification document...

        Retrieves the .txt file which defines this specification,
        allowing us to review the document locally in order to provide
        a reasonable wrapping of it...
        """
        if self.registry.feature:
            return Specification('')
        specFile = self.specFile()
        if os.path.exists(specFile):
            data = open(specFile, 'rb').read()
            return Specification(data)
        else:
            log.info("No spec-file in %s", specFile)
            return Specification('')

    def generate(self):
        for target in (self.rawPathName, self.pathName):
            directory = os.path.dirname(target)
            if not os.path.exists(directory):
                log.warning('Creating target directory: %s', directory)
                os.makedirs(directory)
            if not os.path.isfile(os.path.join(directory, '__init__.py')):
                open(os.path.join(directory, '__init__.py'), 'w').write(
                    '''"""OpenGL Extensions"""'''
                )

        directory = os.path.dirname(self.rawPathName)
        current = ''
        toWrite = self.RAW_MODULE_TEMPLATE % self
        try:
            current = open(self.rawPathName, 'r').read()
        except Exception as err:
            pass
        if current.strip() != toWrite.strip():
            fh = open(self.rawPathName, 'w')
            fh.write(toWrite)
            fh.close()
        if isinstance(self.registry, xmlreg.Feature):
            # this is a core feature...
            target = os.path.join(
                self.overall.rawTargetDirectory, self.prefix, '_glgets.py'
            )
            open(target, 'w').write(self.overall.group_sizes())
        if self.shouldReplace():
            # now the final module with any included custom code...
            toWrite = self.FINAL_MODULE_TEMPLATE % self
            current = ''
            try:
                current = open(self.pathName, 'r').read()
            except Exception as err:
                pass
            else:
                found = current.rfind('\n' + AUTOGENERATION_SENTINEL_END)
                if found >= -1:
                    if current[:found].strip() == toWrite.strip():
                        # we aren't going to change anything...
                        return False
                    found += len('\n' + AUTOGENERATION_SENTINEL_END)
                    current = current[found:]
                else:
                    current = ''
            try:
                fh = open(self.pathName, 'w')
            except IOError as err:
                log.warning("Unable to create module for %r %s", self.name, err)
                return False
            else:
                fh.write(toWrite)
                fh.write(AUTOGENERATION_SENTINEL_END)
                fh.write(current)
                fh.close()
                return True
        return False


class Specification(object):
    """Parser for parsing OpenGL specifications for interesting information"""

    def __init__(self, source):
        """Store the source text for the specification"""
        if isinstance(source, bytes):
            try:
                self.source = source.decode('utf-8')
            except UnicodeDecodeError as err:
                self.source = source.decode('latin-1')
        else:
            self.source = source
        assert isinstance(self.source, unicode)

    def blocks(self, data):
        """Retrieve the set of all blocks"""
        data = data.splitlines()
        title = []
        block = []
        for line in data:
            if line and line.lstrip() == line:
                if block:
                    yield "\n".join(title), textwrap.dedent("\n".join(block))
                    title = []
                    block = []
                title.append(line)
            else:
                block.append(line)
        if block:
            yield "\n".join(title), textwrap.dedent("\n".join(block))

    def constantBlocks(self):
        """Retrieve the set of constant blocks"""
        for title, block in self.blocks(self.source):
            if title and title.startswith('New Tokens'):
                yield block

    def glGetConstants(self):
        """Retrieve the set of constants which pass to glGet* functions"""
        table = {}
        for block in self.constantBlocks():
            for title, section in self.blocks(block):
                for possible in (
                    'GetBooleanv',
                    'GetIntegerv',
                    '<pname> of Get',
                    '<pname> parameter of Get',
                ):
                    if possible in title:
                        for line in section.splitlines():
                            line = line.strip().split()
                            if len(line) == 2:
                                constant, value = line
                                constant = constant.strip(':')
                                table['GL_%s' % (constant,)] = value
                        break
        return table


def download(url):
    """Download the given url, informing the user of what we're doing"""
    log.info(
        'Download: %r',
        url,
    )
    file = urllib.urlopen(url)
    return file.read()
