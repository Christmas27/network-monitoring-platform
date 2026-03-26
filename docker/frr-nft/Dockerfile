FROM frrouting/frr:latest

# FRR image is Alpine in your environment
RUN apk update && apk add --no-cache nftables

# Optional: quick visibility
RUN nft --version || true