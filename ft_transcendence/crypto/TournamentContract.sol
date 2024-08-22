// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


contract TournamentContract{
    
    address owner;


    constructor(){
        owner = msg.sender;
    }

    struct Tournament
    {
        string creator;

        string player1;
        string player2;
        string player3;
        string player4;

        uint8 score1_1;
        uint8 score1_2;

        uint8 score2_1;
        uint8 score2_2;

        uint8 score3_1;
        uint8 score3_2;
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
        string memory player1, 
        string memory player2, 
        string memory player3, 
        string memory player4,
        uint8 score1_1, uint8 score1_2,
        uint8 score2_1, uint8 score2_2,
        uint8 score3_1, uint8 score3_2) 
        public onlyOwner
    {
        Tournament memory newTournament = Tournament(creator, player1, player2, player3, player4, score1_1, score1_2, score2_1, score2_2, score3_1, score3_2);
        tournaments.push(newTournament);
        map[creator].push(newTournament);
    }

}
