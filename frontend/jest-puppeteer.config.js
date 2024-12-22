module.exports = {
    launch: {
        defaultViewport: {
            width: 1680,
            height: 1000,
        },
        headless: process.env.HEADLESS !== "false",
        // chrome sandbox does not work inside container
        args: ["--no-sandbox"],
    },
};
