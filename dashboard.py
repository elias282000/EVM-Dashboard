import streamlit as st
from web3 import Web3
from dotenv import load_dotenv
import json
import os
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import random

# ─────────────────────────────────────────────
# Edit this dict to add/remove/rename candidates.
# Key = candidateId passed to the contract, Value = display name.
# ─────────────────────────────────────────────
CANDIDATES = {
    1: "Candidate 1",
    2: "Candidate 2",
    3: "Candidate 3",
}

def main():
    load_dotenv()
    eth_node_url = os.getenv('ETHEREUM_NODE_URL')
    contract_address = os.getenv('CONTRACT_ADDRESS')

    st.write("Ethereum Node URL:", eth_node_url)
    st.write("Contract Address:", contract_address)

    w3 = Web3(Web3.HTTPProvider(eth_node_url))

    if not w3.is_connected():
        st.error("Failed to connect to Ethereum network!")
        return

    st.write("Connected to Ethereum network")
    st.write("Current block number:", w3.eth.block_number)

    if not w3.is_address(contract_address):
        st.error("Invalid contract address!")
        return

    contract_address = Web3.to_checksum_address(contract_address)

    try:
        with open('contracts/BallotContract.json', 'r') as f:
            contract_data = json.load(f)
            contract_abi = contract_data['abi']
            st.write("Contract ABI loaded successfully")
    except Exception as e:
        st.error(f"Error loading contract ABI: {str(e)}")
        return

    try:
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        st.write("Contract initialized successfully")
    except Exception as e:
        st.error(f"Error initializing contract: {str(e)}")
        return

    st.title("EVM Voting Dashboard")

    try:
        total_votes = contract.functions.getBallotCount().call()
        st.metric("Total Votes Cast", total_votes or 0)
    except Exception as e:
        st.error(f"Error fetching total votes: {str(e)}")

    # ── Dynamic candidate vote fetching ──────────────────────────────────────
    candidate_names = []
    candidate_votes = []

    for candidate_id, candidate_name in CANDIDATES.items():
        try:
            votes = contract.functions.getCandidateVotes(candidate_id).call()
        except Exception as e:
            votes = 0
            st.error(f"Error fetching votes for {candidate_name}: {str(e)}")
        candidate_names.append(candidate_name)
        candidate_votes.append(votes)
    # ─────────────────────────────────────────────────────────────────────────

    total = sum(candidate_votes)

    st.subheader("Vote Count Table")
    vote_data = {
        'Candidate': candidate_names,
        'Votes': candidate_votes,
        'Percentage': [
            f"{(v / total * 100):.2f}%" if total > 0 else "0.00%"
            for v in candidate_votes
        ],
    }
    st.table(pd.DataFrame(vote_data))

    st.subheader("Vote Distribution")
    fig = go.Figure(data=[go.Pie(labels=candidate_names, values=candidate_votes)])
    st.plotly_chart(fig)

    st.subheader("Recent Votes")
    try:
        event_signature = Web3.keccak(text="BallotCast(bytes,uint256)").hex()
        if not event_signature.startswith('0x'):
            event_signature = '0x' + event_signature

        logs = w3.eth.get_logs({
            'address': contract_address,
            'fromBlock': '0x0',
            'toBlock': 'latest',
            'topics': [event_signature],
        })

        if not logs:
            st.info("No voting events found")
        else:
            vote_records = []
            for log in logs:
                decoded_log = contract.events.BallotCast().process_log(log)
                vote_records.append({
                    'Block Number': log['blockNumber'],
                    'Ballot Signature(Hex)': decoded_log['args']['ballotSignature'].hex(),
                })

            random.shuffle(vote_records)
            st.table(pd.DataFrame(vote_records))

    except Exception as e:
        st.error(f"Error fetching recent events: {str(e)}")
        st.error(f"Current block: {w3.eth.block_number}")

if __name__ == "__main__":
    main()