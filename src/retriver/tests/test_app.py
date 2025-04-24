from __future__ import annotations

import asyncio
import unittest

from application.retriver_application import ApplicationInput
from application.retriver_application import ApplicationOutput
from application.retriver_application import RetriveApplication
from shared.utils import get_settings


class TestApp(unittest.TestCase):
    def test_application(self):
        settings = get_settings()
        retrive_service = RetriveApplication(settings=settings)

        # Create the event loop
        loop = asyncio.get_event_loop()

        # Run the task and get the result
        result = loop.run_until_complete(
            retrive_service.process(
                ApplicationInput(
                    query='Cho tôi vài thông tin về mô hình BERT',
                ),
            ),
        )

        # Assertions to validate the result
        self.assertIsInstance(result, ApplicationOutput)
        self.assertIsInstance(result.answer, str)
        self.assertTrue(len(result.answer) > 0, 'Answer should not be empty')

        # Optional: Print the result for debugging
        print(f'Answer: {result.answer}')


if __name__ == '__main__':
    unittest.main()
