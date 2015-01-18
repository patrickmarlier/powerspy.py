#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import powerspy

class Simulator:
  answers = {
              '<S>' : '<K>',
              '<C>' : '<K>',
              '<F>' : '<F4E20>',
#              '<A>' : '<A20513180...>',
#              '<?>' : '<POWERSPYR010102014567>',
               '<?>' : '<POWERSPYC01FF35020001>',
'<V01>' : '<54>',
'<V02>' : '<6C>',
'<V03>' : '<02>',
'<V04>' : '<A7>',
'<V05>' : '<3D>',
'<V06>' : '<CE>',
'<V07>' : '<DC>',
'<V08>' : '<0E>',
'<V09>' : '<3A>',
'<V0E>' : '<6C>',
'<V0F>' : '<02>',
'<V10>' : '<A7>',
'<V11>' : '<3D>',
'<V12>' : '<CE>',
'<V13>' : '<DC>',
'<V14>' : '<0E>',
'<V15>' : '<3A>',
'<Q>' : '<K>',
#'<C>':'<Z>',
'<C>':'<K>',
'<J0032>':'<K><007A1FCA 001F82FB 003AC29C 0FA9 0AB5>'+chr(0x0a)+chr(0x0d)
+'<007656F4 001CF0BF 00379ECF 0F2E 09DA>'+chr(0x0a)+chr(0x0d)
+'<007650A7 001C1FEB 003688C2 0F2F 09EE>'+chr(0x0a)+chr(0x0d)
+'<00765D23 001D2704 00378BCB 0F2F 0A00>'+chr(0x0a)+chr(0x0d)
+'<00766B6A 001B26BF 0035D7A8 0F2F 0957>'
,
'<J32>':'<K><007A1FCA 001F82FB 003AC29C 0FA9 0AB5>'+chr(0x0a)+chr(0x0d)
+'<007656F4 001CF0BF 00379ECF 0F2E 09DA>'+chr(0x0a)+chr(0x0d)
+'<007650A7 001C1FEB 003688C2 0F2F 09EE>'+chr(0x0a)+chr(0x0d)
+'<00765D23 001D2704 00378BCB 0F2F 0A00>'+chr(0x0a)+chr(0x0d)
+'<00766B6A 001B26BF 0035D7A8 0F2F 0957>'

            }
  answer = None

  def close(self):
    pass

  def recv(self, size = 1):
    a = self.answer[0:size]
    self.answer = self.answer[size:]
    return a

  def sendall(self, s):
    # FIXME if not exists...
    try:
      self.answer = self.answers[s]
    except:
      self.answer = '<Z>'

  def settimeout(self, t):
    pass

  def test(self):
    self.sendall('<?>')
    print(self.recv(23))
    self.sendall('<S>')
    print(self.recv())
    print(self.recv())
    print(self.recv())
    self.sendall('<V01>')
    print(self.recv(4))
    # Some distrubing tests
    self.sendall('<V01>')
    print(self.recv(5))

 
if __name__ == '__main__':
  sim = Simulator()
  sim.test()

