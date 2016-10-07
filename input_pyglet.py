import pyglet
import flatbuffers
import inspect
import math
import time
from MoltenGamepad import Event
from MoltenGamepad.Type import Type
from multiprocessing import Process, Queue
from nanomsg import Socket, PAIR, PUB
import signal


def pyglet_process(queue):
	button_mapping = {
		0 : "a",
		1 : "b",
		2 : "x",
		3 : "y",
		4 : "tl",
		5 : "tr",
		6 : "select",
		7 : "start",
		8 : "thumbl",
		9 : "thumbr",
		"x" : "left_x",
		"y" : "left_y",
		"z" : "tl2_axis",
		"rx" : "right_x",
		"ry" : "right_y",
		"rz" : "tr2_axis",
		"dpad_x" : "dpad_x",
		"dpad_y" : "dpad_y"
	}

	joysticks = pyglet.input.get_joysticks()
	if joysticks:
	    joystick = joysticks[0]
	joystick.open()

	def create_fb_event(type=Type.Syn, code="", value=0):
		builder = flatbuffers.Builder(0)
		code_string = builder.CreateString(code)
		Event.EventStart(builder)
		Event.EventAddCode(builder, code_string)
		Event.EventAddType(builder, type)
		Event.EventAddVal(builder, value)
		event = Event.EventEnd(builder)
		builder.Finish(event)
		return str(builder.Output())

	def send_event(type, button, value):
		if button in button_mapping:
			try:
				queue.put(create_fb_event(type, button_mapping[button], value), False)
				queue.put(create_fb_event(), False)
			except Queue.Full:
				pass

	class JoystickHandler(object):
		def on_joybutton_press(self, joystick, button):
			print "button", button
			send_event(Type.Btn, button, 1)

		def on_joybutton_release(self, joystick, button):
			send_event(Type.Btn, button, 0)

		def on_joyaxis_motion(self, joystick, axis, value):
			print axis, value
			send_event(Type.Abs, axis, value*32767)

		def on_joyhat_motion(self, joystick, hat_x, hat_y):
			print "hats ", hat_x, hat_y
			send_event(Type.Abs, "dpad_x", hat_x)
			send_event(Type.Abs, "dpad_y", hat_y)

	def sigint_handler(_1, _2):
		pyglet.app.exit()

	signal.signal(signal.SIGINT, sigint_handler)

	joystick.push_handlers(JoystickHandler())

	pyglet.app.run()

def send_job(queue):
	socket = Socket(PAIR)
	socket.connect("tcp://127.0.0.1:55056")
	while True:
		err = socket.send(queue.get())
		if err:
			print err


def run():
	send_queue = Queue()
	send_proc = Process(target=send_job, args=(send_queue,))
	pyglet_proc = Process(target=pyglet_process, args=(send_queue,))
	send_proc.daemon = True
	pyglet_proc.daemon = True
	try:
		send_proc.start()
		pyglet_proc.start()
		while True:
			time.sleep(1000)
	finally:
		pyglet.app.exit()
		send_proc.terminate()

if __name__ == '__main__':
	run()