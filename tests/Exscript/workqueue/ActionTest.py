import sys, unittest, re, os.path, threading, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from Exscript.workqueue import Action

class FakeMainLoop(object):
    sleep_notified  = False
    wake_notified   = False
    wait_for_called = False

    def _action_sleep_notify(self, action):
        self.sleep_notified = True

    def _action_wake_notify(self, action):
        self.wake_notified = True

    def wait_for(self, action):
        self.wait_for_called = True

class TestAction(Action):
    """
    This action just burns some time using shared data. This is mainly
    because this class is re-used in WorkQueueTest, where we need to stress
    the workqueue.
    """
    id = 0

    def __init__(self, lock, data):
        self.__class__.id += 1
        Action.__init__(self, name = "action %s" % self.__class__.id)
        self.lock = lock
        self.data = data

    def execute(self):
        # Init the data, if it isn't already initialized.
        self.lock.acquire()
        if not self.data.has_key('sum'):
            self.data['sum'] = 0
        if not self.data.has_key('randsum'):
            self.data['randsum'] = 0
        self.lock.release()

        # Manipulate the data.
        self.lock.acquire()
        self.data['sum'] += 1
        self.lock.release()

        # Make sure to lock/unlock many times.
        for number in range(random.randint(0, 4567)):
            self.lock.acquire()
            self.data['randsum'] += number
            self.lock.release()
        return True

class ActionTest(unittest.TestCase):
    CORRELATE = Action

    def setUp(self):
        TestAction.id = 0

    def testConstructor(self):
        action = Action()
        self.assertEqual(None, action.name)
        self.assertEqual(0,    action.debug)

        action = Action(name = 'test', debug = 1)
        self.assertEqual('test', action.name)
        self.assertEqual(1,      action.debug)

    def testWaitFor(self):
        action = Action()
        loop   = FakeMainLoop()
        action._mainloop_added_notify(loop)
        action.wait_for(object)
        self.assert_(loop.sleep_notified)
        self.assert_(loop.wake_notified)
        self.assert_(loop.wait_for_called)

    def testExecute(self):
        action = Action()
        action.execute()

        data   = {'sum': 0, 'randsum': 0}
        action = TestAction(threading.Lock(), data)
        self.assertEqual(action.name, 'action 1')
        self.assertEqual(action.debug, 0)
        action.execute()

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ActionTest)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())