# Federation

Federation is verification-first. A node may learn that peer state differs, but it independently fetches and verifies signed manifests/updates, checks lineage, detects forks, classifies drift and makes a local decision. PolicyMesh intentionally avoids treating peer propagation as automatic authority transfer.
