#!/opt/sw1/intern/jhub-python/3.11.8/node-v17.9.1/bin/node

/**
 * Notebook retrieval and decoding script.
 */

const { readdirSync, readFileSync, existsSync, writeFileSync } = require("fs");
const { join, basename } = require("path");
const { log, error } = require("console");


/**
 * Helper to scan the deployment directory for notebooks.
 */
const getNotebooks = deployDir => {
    let notebooks = {};

    // scan contents of the deployment directory
    readdirSync(deployDir, {withFileTypes: true}).forEach(entry => {
        // must be a file
        if (!entry.isFile()) return;
        // must start with two digits followed by an underscore
        const m = entry.name.match(/^(\d\d(_exercise|_lecture)?)_.*$/);
        if (m === null) return;

        // extract short name (everything but the trailing notebook name)
        const shortName = m[1];
        // store the pair
        notebooks[shortName] = join(deployDir, entry.name);
    });

    return notebooks;
};

/**
 * Obfuscation helpers
 */
const enc = s => {
    return Buffer.from(s, "utf8").toString("base64");
};

const dec = s => {
    return Buffer.from(s, "base64").toString("utf8");
};


/**
 * Helper to provide a notebook.
 */

const provideNotebook = notebookPath => {
    // determine the output path
    const outputPath = join(process.cwd(), basename(notebookPath)) + ".ipynb";

    // the file should not exist already
    if (existsSync(outputPath)) {
        throw new Error(`output path '${outputPath}' already exists`);
    }

    // read the file content
    let content = readFileSync(notebookPath, "utf8");

    // strip trailing newline
    if (content.endsWith("\n")) {
        content = content.slice(0, -1);
    }

    // base64 decode
    content = dec(content);

    // replace DUMMYUSER with username
    const un = process.env.USER;
    content = content.replaceAll(dec("RFVNTVlVU0VS"), un);

    // and again with the username in base64 encoding
    content = content.replaceAll(dec("RFVNTVk2NFVTRVI="), enc(un));

    // write the content to the output file
    writeFileSync(outputPath, content);
    log(`created '${outputPath}'`);
}


/**
 * Main.
 */

const main = async () => {
    // get notebooks
    const deployDir = dec("L2Fmcy9waHlzbmV0LnVuaS1oYW1idXJnLmRlL3VzZXJzL2V4X2JhL21yaWVnZXIvcHVibGljLy5weXRob24tc3MyNS1zZW1lc3Rlci1kZXBsb3ltZW50");
    const notebooks = getNotebooks(deployDir);

    // get arguments
    const args = process.argv.slice(2);
    if (args.length > 1) {
        throw new Error("too many arguments, pass either no or a single argument");
    }

    // print notebooks if there are no arguments
    if (args.length === 0) {
        log("available notebooks:");
        for (const shortName of Object.keys(notebooks).sort()) {
            log(shortName);
        }
        return 0;
    }

    // provide the notebook if it exists
    const shortName = args[0];
    if (!(shortName in notebooks)) {
        throw new Error(`notebook '${shortName}' unknown`);
    }

    // provide the notebook
    provideNotebook(notebooks[shortName]);

    return 0;
}


/**
 * Entry point.
 */

(async () => {
    try {
        process.exitCode = await main();
    } catch (e) {
        error(process.env.ABK_DEBUG === "1" ? e : e.message);
        process.exitCode = 1;
    }
})();
