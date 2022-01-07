# spotify-liked-songs-manager
The original intention of this project was to clean up my Liked Songs in Spotify
by removing songs that aren't played often, and to add songs that I always forget to
save because I'm in the middle of work or on a run.

After looking through the API docs, I got side tracked and the features I've built
thus far are
1. Save TOP10 songs played once a week
2. Save recently played songs once a week

## TODOs

- [ ] Like Songs Manager
	- [ ] set up a DB to save stats on songs I'm listening to
	- [ ] frequently hit Recently Played API to populate DB
	- [ ] learn how to extract patterns from stats to make decisions on how to 
		add or remove songs
- [ ] Group Like Songs into playlist
	- [ ] learn how to extract patterns from stats to make decisions
	- [ ] if this works well, maybe remove songs from Liked Songs when adding to new playlist
- [ ] Create a FE to 
	- [ ] display stats graphs
	- [ ] let other people auth and use this script
- [ ] Learn from reddit feedback
	- [ ] better design patterns, naming, abstractions, commenting
	- [ ] could I work as a freelancer with this level of code?
	- [ ] tips for
		- [ ] logging errors & outputs
		- [ ] running recurring crons, without my laptop having to be on
		- [ ] linting, tooling to speed up python dev
