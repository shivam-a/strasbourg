from daily_activity_pattern import _generate_chain
from data_analysis import _data_analysis
from location_of_activity import _generate_location
from time_of_day import _generate_time

if __name__ == '__main__':
    _generate_chain()
    _generate_time()
    _generate_location()
    _data_analysis()