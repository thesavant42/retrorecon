module.exports = {
  rules: {
    // other stylelint rules here
    // DO NOT globally disable 'no-inline-styles'
  },
  overrides: [
    {
      files: ['templates/index.html'],
      rules: {
        'no-inline-styles': null, // allow inline styles in this file only
      },
    },
  ],
};
