CXX=distcc #g++
DISTCC_HOSTS=10.0.137.2 10.0.137.3 10.0.137.4
CXXFLAGS = -I"/usr/include/opencv"
LINKFLAGS = -lcxcore -lcv -lcvaux -lml -lhighgui

%.o: %.cpp
	@echo $@
	@$(CXX) $(CXXFLAGS) -o $@ $< $(LINKFLAGS)