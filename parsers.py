from abc import ABC, abstractmethod
import logging


logging.basicConfig(filename='stuff_finder.log', level=logging.INFO)


class BaseParser(ABC):

    @abstractmethod
    def parse_ids(self, start_page=1):
        pass

    @abstractmethod
    def get_specs(self, product_id):
        pass

    @abstractmethod
    def process_data(self, data):
        pass

    @abstractmethod
    def save_to_db(self, data):
        pass

    @abstractmethod
    def parse_all(self):
        pass
