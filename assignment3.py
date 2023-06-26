import csv
import random
import pandas as pd
from helper import create_plot
from sim_parameters import TRASITION_PROBS, HOLDING_TIMES

# Function to create samples for each country based on population and age group
def create_samples(countries, country_data, sample_ratio):
    samples = []
    # Filter country data for selected countries
    country_data = country_data.set_index('country').loc[countries].reset_index()
    for _, data in country_data.iterrows():
        population = data['population']
        num_samples = int(population / sample_ratio)
        age_group_names = ['less_5', '5_to_14', '15_to_24', '25_to_64', 'over_65']
        # Calculate the number of samples per age group
        age_group_counts = [int(num_samples * data[name] / 100) for name in age_group_names]

        country = data['country']
        # Create a list of samples with age group and country information
        for age_group_name, count in zip(age_group_names, age_group_counts):
            for _ in range(count):
                samples.append({'country': country, 'age_group': age_group_name})

    return samples

# Function to run the simulation
def run_simulation(samples, start_date, end_date):
    time_range = pd.date_range(start=start_date, end=end_date, freq='D')
    timeline = []

    # Iterate through each person in the sample
    for person_id, sample in enumerate(samples):
        age_group = sample['age_group']
        country = sample['country']
        state = 'H'
        prev_state = None
        staying_days = 0
        holding_days = []

        # Iterate through each day in the time range
        for date in time_range:
            date_str = date.strftime('%Y-%m-%d')
            if date_str == start_date:
                new_state = state
                prev_state = state
            else:
                if staying_days == 0:
                    # Determine the new state based on transition probabilities
                    state_probs = TRASITION_PROBS[age_group][state]
                    new_state = random.choices(list(state_probs.keys()), weights=list(state_probs.values()), k=1)[0]
                    staying_days = HOLDING_TIMES[age_group][new_state]
                else:
                    new_state = state
                    staying_days -= 1

                if staying_days == 1:
                    holding_days.clear()
                elif staying_days > 1:
                    holding_days = [staying_days - 1]

                prev_state = state

            # Add the current state to the timeline
            timeline.append({'person_id': person_id, 'age_group': age_group, 'country': country,
                             'date': date_str, 'state': new_state, 'staying_days': staying_days, 'prev_state': prev_state})

            state = new_state
    return timeline

# Function to save the simulation results to a CSV file
def save_simulation_csv(timeline, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['person_id', 'age_group', 'country', 'date', 'state', 'staying_days', 'prev_state']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(timeline)

# Function to save the summary of the simulation to a CSV file
def save_summary_csv(timeline, countries, output_file):
    df = pd.DataFrame(timeline)
    summary = df.groupby(['date', 'country', 'state']).size().reset_index(name='count')
    summary = summary.pivot_table(index=['date', 'country'], columns='state', values='count', fill_value=0).reset_index()

    if summary['date'].dtypes != 'object':
        summary['date'] = summary['date'].dt.strftime('%Y-%m-%d')
    summary.to_csv(output_file, index=False)

# Function to run the entire process
def run(countries_csv_name, countries, start_date, end_date, sample_ratio):
    country_data = pd.read_csv(countries_csv_name)
    samples = create_samples(countries, country_data, sample_ratio)
    timeline = run_simulation(samples, start_date, end_date)

    # Save simulation and summary results to CSV files
    save_simulation_csv(timeline, 'a3-covid-simulated-timeseries.csv')
    save_summary_csv(timeline, countries, 'a3-covid-summary-timeseries.csv')
    # Create a plot for the selected countries
    create_plot('a3-covid-summary-timeseries.csv', countries)

