# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:28:15 2017

@author: marzipan
"""

import asyncio
import unittest
import inspect
import logging

import simplejson as json

from AlphaScanClientServer.Server.CommandServerResponses import CommandServerResponses
from AlphaScanClientServer.Stubs.stub_websockets import stub_websockets

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class ErrorsTestCase(unittest.TestCase):
    def setUp(self):
        self.ws = stub_websockets()
        self.err = CommandServerResponses(self.ws)

        # Get all of the member names and functions in the error class        
        self.err_members = inspect.getmembers(self.err, predicate=inspect.ismethod)
        self.err_member_names = [name_str for name_str,func in self.err_members if name_str[0] != "_"] # underscored methods represent internal functions
        self.err_member_functions = [func for name_str,func in self.err_members if name_str[0] != "_"]

    def test_ErrorCodeListContainsAllErrorFunctions(self):        
        # Make sure the length of the list of members is equal to the length of the ERRORS array
        self.assertEqual(len(self.err_member_names), len(self.err.ERRORS))
        # If it is, then as long as all functions are in the list (b/c function names are unique)
        # then they are equal
        for n in self.err_member_names:
            self.assertIn(n, self.err.ERRORS)
            
    def test_ErrorFunctionsSendCorrectErrorCodes(self):
        data = [None, "", 1, [1],["1"],{},True]
        data_idx = 0
        for name, func in self.err_members:
            if name[0] != "_": #exclude internal class methods
                _run(func(data=data[data_idx])) #send error code to dummy WS object
                correct_response = json.dumps({"RESP":name, "CODE":self.err.ERRORS[name][0], "MSG":"","DATA":data[data_idx]})
                self.assertEqual(correct_response, self.ws.last_sent)
                data_idx = (data_idx + 1) % len(data) 
    
    def test_ErrorFunctionsReturnCorrectErrorCodes(self):
        for name, func in self.err_members:
            if name[0] != "_":
                self.assertEqual(self.err.ERRORS[name][0], _run(func()))
                
    def test_ErrorLogLevelsAreValid(self):
        for v in self.err.ERRORS.values():
            self.assertIn(v[1], self.err.LOG_LEVELS.keys())
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()