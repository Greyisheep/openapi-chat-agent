#!/usr/bin/env node

/**
 * Postman Collection Test Runner
 * 
 * This script runs the OpenAPI Chat Agent API collection using Newman
 * for automated testing in CI/CD pipelines.
 * 
 * Usage:
 *   node postman-tests.js [options]
 * 
 * Options:
 *   --env <file>     Environment file (default: OpenAPI_Chat_Agent_Environment.postman_environment.json)
 *   --collection <file> Collection file (default: OpenAPI_Chat_Agent_API.postman_collection.json)
 *   --base-url <url> Base URL for testing (default: http://localhost:8000)
 *   --reporters <list> Newman reporters (default: cli,json)
 *   --bail           Stop on first failure
 *   --delay <ms>     Delay between requests (default: 1000)
 */

const newman = require('newman');
const path = require('path');
const fs = require('fs');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
    env: 'OpenAPI_Chat_Agent_Environment.postman_environment.json',
    collection: 'OpenAPI_Chat_Agent_API.postman_collection.json',
    baseUrl: 'http://localhost:8000',
    reporters: ['cli', 'json'],
    bail: false,
    delay: 1000
};

for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
        case '--env':
            options.env = args[++i];
            break;
        case '--collection':
            options.collection = args[++i];
            break;
        case '--base-url':
            options.baseUrl = args[++i];
            break;
        case '--reporters':
            options.reporters = args[++i].split(',');
            break;
        case '--bail':
            options.bail = true;
            break;
        case '--delay':
            options.delay = parseInt(args[++i]);
            break;
        case '--help':
            console.log(`
Postman Collection Test Runner

Usage: node postman-tests.js [options]

Options:
  --env <file>        Environment file (default: OpenAPI_Chat_Agent_Environment.postman_environment.json)
  --collection <file> Collection file (default: OpenAPI_Chat_Agent_API.postman_collection.json)
  --base-url <url>    Base URL for testing (default: http://localhost:8000)
  --reporters <list>  Newman reporters (default: cli,json)
  --bail              Stop on first failure
  --delay <ms>        Delay between requests (default: 1000)
  --help              Show this help message

Examples:
  node postman-tests.js
  node postman-tests.js --base-url https://api.example.com
  node postman-tests.js --reporters cli,html --bail
            `);
            process.exit(0);
    }
}

// Validate files exist
const collectionPath = path.resolve(options.collection);
const envPath = path.resolve(options.env);

if (!fs.existsSync(collectionPath)) {
    console.error(`❌ Collection file not found: ${collectionPath}`);
    process.exit(1);
}

if (!fs.existsSync(envPath)) {
    console.error(`❌ Environment file not found: ${envPath}`);
    process.exit(1);
}

console.log('🚀 Starting Postman Collection Tests');
console.log(`📁 Collection: ${options.collection}`);
console.log(`🌍 Environment: ${options.env}`);
console.log(`🔗 Base URL: ${options.baseUrl}`);
console.log(`📊 Reporters: ${options.reporters.join(', ')}`);
console.log(`⏱️  Delay: ${options.delay}ms`);
console.log(`🛑 Bail on failure: ${options.bail}`);
console.log('');

// Configure Newman options
const newmanOptions = {
    collection: collectionPath,
    environment: envPath,
    reporters: options.reporters,
    delayRequest: options.delay,
    bail: options.bail,
    globalVar: [
        {
            key: 'base_url',
            value: options.baseUrl
        }
    ],
    // Custom reporter for JSON output
    reporter: {
        json: {
            export: './test-results.json'
        },
        html: {
            export: './test-results.html'
        }
    }
};

// Run Newman
newman.run(newmanOptions, (err, summary) => {
    if (err) {
        console.error('❌ Newman execution failed:', err);
        process.exit(1);
    }

    console.log('\n📊 Test Results Summary:');
    console.log(`✅ Passed: ${summary.run.stats.assertions.passed}`);
    console.log(`❌ Failed: ${summary.run.stats.assertions.failed}`);
    console.log(`⏭️  Skipped: ${summary.run.stats.assertions.skipped}`);
    console.log(`📝 Total: ${summary.run.stats.assertions.total}`);
    console.log(`⏱️  Duration: ${summary.run.timings.completed - summary.run.timings.started}ms`);

    // Check for failures
    if (summary.run.failures.length > 0) {
        console.log('\n❌ Test Failures:');
        summary.run.failures.forEach((failure, index) => {
            console.log(`${index + 1}. ${failure.source.name}: ${failure.error.message}`);
        });
        process.exit(1);
    }

    console.log('\n🎉 All tests passed!');
    process.exit(0);
});
