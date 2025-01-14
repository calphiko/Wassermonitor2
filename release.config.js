module.exports = {
  "branches": ['main'],
  "repositoryUrl": "https://github.com/calphiko/Wassermonitor2",
  "tagFormat": "v${version}",
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    "@semantic-release/git"
  ]
};
