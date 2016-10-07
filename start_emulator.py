import envoy
r = envoy.run("adb devices")
if not "emulator" in r.std_out:
	envoy.connect("emulator -avd android_tv -kernel bzImage")

while envoy.run("adb shell echo yes").status_code != 0:
	pass

envoy.run("adb push moltengamepad /data/")
envoy.run("adb push libnanomsg.so.5.0.0 /data/")
envoy.run("adb shell chmod a+x /data/moltengamepad")
envoy.run("adb forward tcp:55056 tcp:55056")
r = envoy.run("adb shell ps")
print r.std_out
if not "moltengamepad" in r.std_out:
	molten = envoy.connect("adb shell LD_LIBRARY_PATH=/data/ /data/moltengamepad")
	print molten.std_out


if __name__ == '__main__':
	import input_pyglet

	input_pyglet.run()
