def main():
    try:
        n = int(input().strip())
        a = list(map(int, input().split()))
    except:
        return
    
    if n == 1:
        print(a[0])
        print(1)
    elif n == 2:
        print(-1)
    else:
        INF = -10**15
        dp = [INF] * (n + 1)
        prev = [-1] * (n + 1)
        
        dp[1] = a[0]
        prev[1] = -1
        
        if n >= 3:
            dp[3] = a[2] + dp[1]
            prev[3] = 1
            
        for i in range(4, n + 1):
            candidates = []
            if i - 2 >= 1 and dp[i - 2] != INF:
                candidates.append((dp[i - 2], i - 2))
            if i - 3 >= 1 and dp[i - 3] != INF:
                candidates.append((dp[i - 3], i - 3))
                
            if candidates:
                best_val, best_prev = max(candidates, key=lambda x: x[0])
                dp[i] = a[i - 1] + best_val
                prev[i] = best_prev
                
        if dp[n] == INF:
            print(-1)
        else:
            path = []
            cur = n
            while cur != -1:
                path.append(cur)
                cur = prev[cur]
            path.reverse()
            print(dp[n])
            print(" ".join(map(str, path)))
main()