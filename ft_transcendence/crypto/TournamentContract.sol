// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TournamentContract{
    
    address owner;


    constructor(){
        owner = msg.sender;
    }

    struct Scores {
        uint8 score1_1;
        uint8 score1_2;
        uint8 score2_1;
        uint8 score2_2;
        uint8 score3_1;
        uint8 score3_2;
    }

    struct Players {
        string player1;
        string player2;
        string player3;
        string player4;
    }

    struct Tournament
    {
        string creator;
        string name;
        uint8  online;


        uint timestamp;
        Scores score;
        Players player;
    }

    Tournament[] private tournaments;

    mapping (string => Tournament[]) private map;

    function getTournaments() public view returns (Tournament[] memory) {
        return tournaments;
    }


    function getTournamentsByCreator(string memory login) public view returns (Tournament[] memory)
    {
        return map[login];
    }


    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    function addTournament(
        string memory creator,
        string memory name,
        uint8 online,
        Players memory player,
        Scores memory score) 
        public onlyOwner
    {
        Tournament memory newTournament = Tournament(creator, name, online, block.timestamp, score, player);
        tournaments.push(newTournament);
        map[creator].push(newTournament);
    }

}
