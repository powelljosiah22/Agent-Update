#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const os = require("os");

// Load .env from ~/Agents/Agent 0/.env
const agent0Dir = path.resolve(__dirname, "../..");
const envPath = path.join(agent0Dir, ".env");
try {
  require("dotenv").config({ path: envPath });
} catch (_) {}

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const { ListToolsRequestSchema, CallToolRequestSchema } = require("@modelcontextprotocol/sdk/types.js");
const { google } = require("googleapis");

const credsDir = process.env.GOOGLE_CREDS_DIR
  ? process.env.GOOGLE_CREDS_DIR.replace(/^~($|\/)/, `${os.homedir()}$1`)
  : path.join(agent0Dir, "credentials");
const gauthPath = path.join(credsDir, "gauth.json");
const defaultUserEmail = process.env.USER_EMAIL || "";

function getDriveClient(userId) {
  if (!fs.existsSync(gauthPath)) {
    throw new Error(`gauth.json not found at ${gauthPath}. See credentials/README_OAUTH.md.`);
  }
  const gauth = JSON.parse(fs.readFileSync(gauthPath, "utf8"));
  const clientConfig = gauth.installed || gauth.web || {};
  const oauth2Client = new google.auth.OAuth2(
    clientConfig.client_id,
    clientConfig.client_secret,
    "http://localhost:4100/code"
  );

  const resolvedUser = userId || defaultUserEmail;
  const tokenPath = path.join(credsDir, `.oauth2.${resolvedUser}.json`);
  if (!fs.existsSync(tokenPath)) {
    throw new Error(`No stored credentials for ${resolvedUser} at ${tokenPath}. Run credentials/generate_token.py first.`);
  }

  const tokens = JSON.parse(fs.readFileSync(tokenPath, "utf8"));
  oauth2Client.setCredentials(tokens);
  return google.drive({ version: "v3", auth: oauth2Client });
}

const server = new Server(
  { name: "mcp-google-drive", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "drive_list_files",
        description: "Lists or searches files in Google Drive for a user.",
        inputSchema: {
          type: "object",
          properties: {
            user_id: { type: "string", description: "Email address of the account (optional if USER_EMAIL is set in .env)" },
            query: { type: "string", description: "Optional Drive query e.g. name contains 'Project' or mimeType = 'application/pdf'" },
            pageSize: { type: "integer", description: "Number of files to return (default 20, max 100)" },
            folderId: { type: "string", description: "Optional parent folder ID to list contents of" }
          }
        }
      },
      {
        name: "drive_get_file_metadata",
        description: "Gets detailed metadata for a specific Google Drive file.",
        inputSchema: {
          type: "object",
          properties: {
            user_id: { type: "string", description: "Email address of the account" },
            fileId: { type: "string", description: "Google Drive File ID" }
          },
          required: ["fileId"]
        }
      },
      {
        name: "drive_read_file_content",
        description: "Reads or exports the text content of a Google Drive file.",
        inputSchema: {
          type: "object",
          properties: {
            user_id: { type: "string", description: "Email address of the account" },
            fileId: { type: "string", description: "Google Drive File ID" },
            exportMimeType: { type: "string", description: "MIME type to export Google Docs/Sheets/Slides (e.g. text/plain, text/csv)" }
          },
          required: ["fileId"]
        }
      },
      {
        name: "drive_create_doc",
        description: "Creates a new Google Doc file with specified title and content.",
        inputSchema: {
          type: "object",
          properties: {
            user_id: { type: "string", description: "Email address of the account" },
            name: { type: "string", description: "Title of the Google Doc" },
            content: { type: "string", description: "Initial text content of the Google Doc" },
            folderId: { type: "string", description: "Optional parent folder ID" }
          },
          required: ["name", "content"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const userId = (args && args.user_id) ? args.user_id : defaultUserEmail;

  try {
    const drive = getDriveClient(userId);

    if (name === "drive_list_files") {
      let q = (args && args.query) ? args.query : "trashed = false";
      if (args && args.folderId) {
        q = `'${args.folderId}' in parents and ${q}`;
      }
      const res = await drive.files.list({
        q,
        pageSize: (args && args.pageSize) ? args.pageSize : 20,
        fields: "files(id, name, mimeType, size, modifiedTime, webViewLink, parents)"
      });
      return {
        content: [{ type: "text", text: JSON.stringify(res.data.files || [], null, 2) }]
      };
    }

    if (name === "drive_get_file_metadata") {
      const res = await drive.files.get({
        fileId: args.fileId,
        fields: "id, name, mimeType, description, size, createdTime, modifiedTime, webViewLink, parents, permissions"
      });
      return {
        content: [{ type: "text", text: JSON.stringify(res.data, null, 2) }]
      };
    }

    if (name === "drive_read_file_content") {
      const meta = await drive.files.get({ fileId: args.fileId, fields: "mimeType, name" });
      const mimeType = meta.data.mimeType || "";

      let contentData;
      if (mimeType.startsWith("application/vnd.google-apps.")) {
        let exportMime = args.exportMimeType || "text/plain";
        if (mimeType.includes("spreadsheet")) exportMime = args.exportMimeType || "text/csv";
        if (mimeType.includes("presentation")) exportMime = args.exportMimeType || "text/plain";

        const res = await drive.files.export({ fileId: args.fileId, mimeType: exportMime }, { responseType: "text" });
        contentData = res.data;
      } else {
        const res = await drive.files.get({ fileId: args.fileId, alt: "media" }, { responseType: "text" });
        contentData = res.data;
      }

      return {
        content: [{ type: "text", text: typeof contentData === "string" ? contentData : JSON.stringify(contentData) }]
      };
    }

    if (name === "drive_create_doc") {
      const reqBody = {
        name: args.name,
        mimeType: "application/vnd.google-apps.document"
      };
      if (args.folderId) {
        reqBody.parents = [args.folderId];
      }
      const res = await drive.files.create({
        requestBody: reqBody,
        media: {
          mimeType: "text/plain",
          body: args.content
        },
        fields: "id, name, mimeType, webViewLink"
      });
      return {
        content: [{ type: "text", text: JSON.stringify(res.data, null, 2) }]
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (err) {
    return {
      isError: true,
      content: [{ type: "text", text: `Drive operation failed: ${err.message}` }]
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal error starting drive MCP server:", err);
  process.exit(1);
});
