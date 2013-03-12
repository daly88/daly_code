#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <time.h>
#include <sys/time.h>

#include <Python.h>
#include <lua.hpp>

#define RUN_BEGIN(x) uint32_t begin_##x, end_##x; \
	begin_##x = timenow();

#define RUN_END(x) end_##x = timenow(); \
	printf("%s used: %.4lf s\n", #x, (double)(end_##x - begin_##x) / 10000.0);
	

//uint: 0.1 ms
uint32_t timenow()
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return tv.tv_sec * 10000 + (tv.tv_usec / 100);
}

//begin python bench
int py_bench()
{
	uint32_t t_begin, t_end;
	Py_Initialize();
	if (!Py_IsInitialized()) {
		printf("python initial fail\n");
		return -1;
	}

	PyRun_SimpleString("import sys");
	PyRun_SimpleString("sys.path.append('./')");


	PyObject *pName, *pModule, *pDict;
	pName = PyString_FromString("py_main");
	pModule = PyImport_Import(pName);
	if (!pModule) {
		printf("load pythong module fail\n");
		return -1;	
	}

	pDict = PyModule_GetDict(pModule);
	if (!pDict) {
		return -1;
	}
	return 0;
}

//begin lua bench
int lua_bench()
{
	int ret = 0;
	lua_State *lstate = lua_open();
	if (lstate == NULL) {
		printf("init lua failed\n");
		return -1;
	}
	ret = luaL_loadfile(lstate, "lua_main.lua");
	if (ret != 0) {
		printf("load lua file failed\n");
		return -1;
	}
	return 0;
}


int main(int argc, char** argv)
{
	RUN_BEGIN(python);
	py_bench();
	RUN_END(python);

	RUN_BEGIN(lua);
	lua_bench();
	RUN_END(lua);
	return 0;
}
