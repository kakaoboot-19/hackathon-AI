GITHUB_QUERY = """
    query($username: String!) {
      user(login: $username) {
        # 기본 정보
        login
        name
        bio
        followers {
          totalCount
        }
        
        # indie/Crew 분석용 데이터
        contributionsCollection {
          # Solo vs Team 활동량
          totalCommitContributions
          totalPullRequestReviewContributions
          totalIssueContributions
          totalPullRequestContributions
          
          # 상세 커밋 데이터
          commitContributionsByRepository(maxRepositories: 10) {
            repository {
              name
            }
            contributions(first: 20) {
              nodes {
                occurredAt
              }
            }
          }
        }
        
        # 기술 스택 분석용
        repositories(first: 10, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
          nodes {
            name
            
            # 각 레포의 최근 커밋 상세 정보
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 20) {
                    edges {
                      node {
                        committedDate
                        message
                        additions
                        deletions
                        changedFilesIfAvailable
                      }
                    }
                  }
                }
              }
            }
            
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
      }
      
      rateLimit {
        limit
        remaining
        resetAt
      }
    }
    """