# filesystem-mcp-server - Directory Structure

Generated on: 2025-05-23 11:54:51


```
filesystem-mcp-server
├── backups
├── docs
    └── tree.md
├── scripts
    ├── clean.ts
    └── tree.ts
├── src
    ├── config
    │   └── index.ts
    ├── mcp-server
    │   ├── tools
    │   │   ├── copyPath
    │   │   │   ├── copyPathLogic.ts
    │   │   │   ├── index.ts
    │   │   │   └── registration.ts
    │   │   ├── createDirectory
    │   │   │   ├── createDirectoryLogic.ts
    │   │   │   ├── index.ts
    │   │   │   └── registration.ts
    │   │   ├── deleteDirectory
    │   │   │   ├── deleteDirectoryLogic.ts
    │   │   │   ├── index.ts
    │   │   │   └── registration.ts
    │   │   ├── deleteFile
    │   │   │   ├── deleteFileLogic.ts
    │   │   │   ├── index.ts
    │   │   │   └── registration.ts
    │   │   ├── listFiles
    │   │   │   ├── index.ts
    │   │   │   ├── listFilesLogic.ts
    │   │   │   └── registration.ts
    │   │   ├── movePath
    │   │   │   ├── index.ts
    │   │   │   ├── movePathLogic.ts
    │   │   │   └── registration.ts
    │   │   ├── readFile
    │   │   │   ├── index.ts
    │   │   │   ├── readFileLogic.ts
    │   │   │   └── registration.ts
    │   │   ├── setFilesystemDefault
    │   │   │   ├── index.ts
    │   │   │   ├── registration.ts
    │   │   │   └── setFilesystemDefaultLogic.ts
    │   │   ├── updateFile
    │   │   │   ├── index.ts
    │   │   │   ├── registration.ts
    │   │   │   └── updateFileLogic.ts
    │   │   └── writeFile
    │   │   │   ├── index.ts
    │   │   │   ├── registration.ts
    │   │   │   └── writeFileLogic.ts
    │   ├── transports
    │   │   ├── authentication
    │   │   │   └── authMiddleware.ts
    │   │   ├── httpTransport.ts
    │   │   └── stdioTransport.ts
    │   ├── server.ts
    │   └── state.ts
    ├── types-global
    │   ├── errors.ts
    │   ├── mcp.ts
    │   └── tool.ts
    ├── utils
    │   ├── internal
    │   │   ├── errorHandler.ts
    │   │   ├── index.ts
    │   │   ├── logger.ts
    │   │   └── requestContext.ts
    │   ├── metrics
    │   │   ├── index.ts
    │   │   └── tokenCounter.ts
    │   ├── parsing
    │   │   ├── dateParser.ts
    │   │   ├── index.ts
    │   │   └── jsonParser.ts
    │   ├── security
    │   │   ├── idGenerator.ts
    │   │   ├── index.ts
    │   │   ├── rateLimiter.ts
    │   │   └── sanitization.ts
    │   └── index.ts
    └── index.ts
├── .clinerules
├── .dockerignore
├── CHANGELOG.md
├── Dockerfile
├── LICENSE
├── mcp.json
├── package-lock.json
├── package.json
├── README.md
├── repomix.config.json
├── smithery.yaml
└── tsconfig.json

```

_Note: This tree excludes files and directories matched by .gitignore and common patterns like node_modules._
