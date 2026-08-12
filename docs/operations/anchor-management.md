# Trust-anchor management

```bash
links anchors register <village> <public-key-b64> <anchor-id>
links anchors rotate <village> <new-public-key-b64> <anchor-id> <previous-key-hash>
links anchors revoke <village> <anchor-id> <anchor-key-hash>
links anchors inspect <village>
links anchors history <village>
```

Rotation and revocation append history. Historical entries are retained so an assurance process can distinguish **authoritative now** from **authoritative at an earlier time**.
