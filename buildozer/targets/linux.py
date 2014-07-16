from buildozer import BuildozerException
from buildozer.target import Target
import os
import shutil

class TargetLinux(Target):

	@property
	def description(self):
		return self.buildozer.config.getdefault('debian','description')
	
	@property
	def long_description(self):
		return self.buildozer.config.getdefault('debian','long_description') 
	
	@property
	def author(self):
		return self.buildozer.config.getdefault('debian','author')
	
	@property
	def author_email(self):
		return self.buildozer.config.getdefault('debian','author_email')
		
	@property
	def package_data(self):
		package_data = self.buildozer.config.getdefault('debian','package_data')
		data = ''
		for packs in package_data.split(','):
			data += '"'+packs+'"'
		return data
	
	@property
	def entry_point(self):
		return self.buildozer.config.getdefault('debian','entry_point')

	def assemble_specs(self):
		self.version = self.buildozer.get_version()
		self.name = self.buildozer.config.get('app','package.name').lower()
		self.url = self.buildozer.config.get('app','package.domain')
		self.P_dependencies = self.buildozer.config.get('debian','P_dependencies')
		self.dependencies = self.buildozer.config.get('debian','dependencies')
		self.requirements = ''
		for dep in self.P_dependencies.split(','):
			self.requirements += 'python-'+dep+','
		for dep in self.dependencies.split(','):
			self.requirements += dep+','
		self.requirements = self.requirements[:-1]  
		self.license = self.buildozer.config.get('debian','license')
		
	def set_directory(self):
		shutil.copytree('.','./build/'+self.name)
		os.chdir('./build/'+self.name)
		
		if not os.path.exists("__init__.py"):
			f = open('__init__.py','w+')
			f.close()
		
		if not os.path.exists("README"):
			f = open('README','w+')
			f.write("*------------*")
			f.close()
		
		shutil.move('README','..')
		os.chdir('..')
		
	def replace_line(self,file_name, line_num, text):
    		lines = open(file_name, 'r').readlines()
    		lines[line_num] = text
    		out = open(file_name, 'w')
    		out.writelines(lines)
    		out.close()

	def create_setup(self,):
		setup = '''
from setuptools import setup, find_packages # Always prefer setuptools over distutils
from codecs import open # To use a consistent encoding
from os import path
here = path.abspath(path.dirname(__file__))
setup(
    name='%s',
    version='%s',
    description='%s',
    long_description="%s",
    url='%s',
    author='%s',
    author_email='%s',
    license='%s',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['pygame','kivy'],
    package_data={
        '': [%s],
    },
    entry_points={
        'console_scripts': [
            '%s'
        ],
    },
)'''%(self.name,self.version,self.description,self.long_description,
	self.url,self.author,self.author_email,self.license,self.package_data,
	self.name+'='+self.name+'.'+self.entry_point+':'+'run')
		f_setup = open('setup.py','w+')
		f_setup.write(setup)
		f_setup.close()
	
	def prepare_build(self):
		os.system('python setup.py sdist')
		os.chdir('dist')
		os.system('py2dsc %s'%(self.name+'-'+self.version+'.tar.gz'))		
		os.chdir('deb_dist')
		os.chdir(self.name+'-'+self.version)
		os.chdir('debian')
		
	def edit_control(self):
		text = 'Depends: ${misc:Depends}, ${python:Depends}, '+self.requirements+'\n'
		self.replace_line('control',9,text)
		text = 'Build-Depends: python-setuptools (>= 0.6b3), python-all (>= 2.7), debhelper (>= 7.4.3)\n'
		self.replace_line('control',4,text)
		
	def clean_build(self):
		os.chdir('..')
		os.system('debuild')
		os.chdir('..')
		shutil.copy('python-%s_%s-1_all.deb'%(self.name,self.version),'../../..')
		os.chdir('../../..')
		if os.path.exists('build'):
			shutil.rmtree('build')
		if os.path.exists('bin'):
			shutil.rmtree('bin')
		self.buildozer.info('Done')
	
	def cmd_build(self,*args):
		super(TargetLinux, self).cmd_build(*args)
		self.buildozer.info('Assembling specs')
		self.assemble_specs()
		self.buildozer.info('Setting up temp directories')
		self.set_directory()
		self.buildozer.info('Creating setup file')
		self.create_setup()
		self.buildozer.info('Creating tarballs')
		self.prepare_build()
		self.buildozer.info('Editing control files')
		self.edit_control()
		self.buildozer.info('Building a package')
		self.clean_build()
		self.buildozer.info('Successfully Build')
		
	
def get_target(buildozer):
    return TargetLinux(buildozer)
